import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from processor import extrair_padrao_regra

load_dotenv()


class DatabaseError(RuntimeError):
    """Erro operacional ao acessar o banco de dados."""


class DatabaseManager:
    """Acesso ao Postgres local (rodando via Docker), sem Supabase.

    App de uso pessoal, single-user, sem autenticação: todas as linhas
    são visíveis para quem acessa a API localmente.
    """

    def __init__(self):
        self.dsn = os.environ.get("DATABASE_URL")
        self.client = bool(self.dsn)  # mantém a checagem "configurado?" usada no resto do código

    @contextmanager
    def _connect(self):
        if not self.dsn:
            raise DatabaseError("Banco de dados não configurado. Defina DATABASE_URL no .env.")
        try:
            conn = psycopg.connect(self.dsn, row_factory=dict_row)
        except Exception as exc:
            raise DatabaseError("Não foi possível conectar ao banco de dados.") from exc
        try:
            yield conn
            conn.commit()
        except DatabaseError:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            raise DatabaseError("Erro ao acessar o banco de dados.") from exc
        finally:
            conn.close()

    def save_transactions(self, transactions: list):
        """Salva uma lista de transações no banco, ignorando duplicatas exatas.

        Uma transação é considerada duplicata quando já existe uma linha com
        a mesma (data, descrição, valor) — o caso típico de reimportar o
        mesmo extrato/fatura duas vezes. Retorna um resumo com as contagens.
        """
        if not transactions:
            return {"inseridas": 0, "duplicadas": 0}

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("select data, descricao, valor from transacoes")
                existentes = {
                    (
                        row["data"].isoformat() if hasattr(row["data"], "isoformat") else row["data"],
                        row["descricao"],
                        round(float(row["valor"]), 2),
                    )
                    for row in cur.fetchall()
                }

                cur.execute("select padrao, categoria from regras_categorizacao")
                regras = {r["padrao"]: r["categoria"] for r in cur.fetchall()}

                inseridas = 0
                duplicadas = 0
                for t in transactions:
                    try:
                        parts = t["data"].split("/")
                        if len(parts) == 3:
                            iso_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        else:
                            iso_date = t["data"]
                    except Exception:
                        iso_date = t["data"]

                    chave = (iso_date, t["descricao"], round(float(t["valor"]), 2))
                    if chave in existentes:
                        duplicadas += 1
                        continue

                    # Regra aprendida (correção manual anterior) tem prioridade
                    # sobre a categorização por palavra-chave do processor.
                    padrao = extrair_padrao_regra(t["descricao"])
                    categoria = regras.get(padrao, t["categoria"])

                    cur.execute(
                        """
                        insert into transacoes (data, descricao, valor, categoria, tipo, fonte)
                        values (%s, %s, %s, %s, %s, %s)
                        """,
                        (iso_date, t["descricao"], t["valor"], categoria, t["tipo"], t["fonte"]),
                    )
                    existentes.add(chave)  # evita duplicar dentro do próprio lote também
                    inseridas += 1

                return {"inseridas": inseridas, "duplicadas": duplicadas}

    def get_transactions(self):
        """Busca todas as transações"""
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("select * from transacoes order by data desc")
                return [dict(row) for row in cur.fetchall()]

    # --- CATEGORIAS ---
    def get_categories(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("select * from categorias")
                return [dict(row) for row in cur.fetchall()]

    def add_category(self, nome, tipo):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "insert into categorias (nome, tipo) values (%s, %s)",
                    (nome, tipo),
                )

    def delete_category(self, id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from categorias where id = %s", (id,))

    def update_category(self, id, nome, tipo):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "update categorias set nome = %s, tipo = %s where id = %s",
                    (nome, tipo, id),
                )

    def add_manual_transaction(self, t):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into transacoes (data, descricao, valor, categoria, tipo, fonte, data_vencimento)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        t["data"],
                        t["descricao"],
                        t["valor"],
                        t["categoria"],
                        t["tipo"],
                        "Manual",
                        t.get("data_vencimento"),
                    ),
                )

    def delete_transaction(self, id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from transacoes where id = %s", (id,))

    def _backup_before_wipe(self):
        """Salva um snapshot JSON de transações+categorias antes de um delete em massa.

        É uma rede de segurança best-effort: se o backup falhar por qualquer
        motivo, isso NUNCA deve impedir o delete que o usuário pediu — apenas
        registra o erro e segue em frente.
        """
        def _serialize(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            return str(obj)

        try:
            snapshot = {"transacoes": self.get_transactions(), "categorias": self.get_categories()}

            backup_dir = Path(__file__).resolve().parent.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
            backup_file = backup_dir / f"pre_delete_all_{timestamp}.json"

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, default=_serialize, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"Aviso: não foi possível gerar backup automático antes do delete-all: {exc}")

    def delete_all_transactions(self):
        self._backup_before_wipe()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from transacoes")

    def update_transaction(self, id, data):
        if not data:
            return
        columns = list(data.keys())
        set_clause = ", ".join(f"{col} = %s" for col in columns)
        values = [data[col] for col in columns] + [id]
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"update transacoes set {set_clause} where id = %s returning descricao",
                    values,
                )
                row = cur.fetchone()

                # Se o usuário corrigiu a categoria manualmente, "aprende" essa
                # correção (por nome de PIX/TED) e aplica retroativamente em
                # outras transações com o mesmo remetente/destinatário que
                # ainda estejam em "A Categorizar".
                nova_categoria = data.get("categoria")
                if nova_categoria and nova_categoria != "A Categorizar" and row:
                    padrao = extrair_padrao_regra(row["descricao"])
                    if padrao and len(padrao) >= 4:
                        cur.execute(
                            """
                            insert into regras_categorizacao (padrao, categoria)
                            values (%s, %s)
                            on conflict (padrao) do update set categoria = excluded.categoria
                            """,
                            (padrao, nova_categoria),
                        )

                        cur.execute(
                            "select id, descricao from transacoes where categoria = 'A Categorizar' and id != %s",
                            (id,),
                        )
                        for candidata in cur.fetchall():
                            if extrair_padrao_regra(candidata["descricao"]) == padrao:
                                cur.execute(
                                    "update transacoes set categoria = %s where id = %s",
                                    (nova_categoria, candidata["id"]),
                                )

    # --- REGRAS DE CATEGORIZAÇÃO APRENDIDAS ---
    def get_category_rules(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("select * from regras_categorizacao order by categoria, padrao")
                return [dict(row) for row in cur.fetchall()]

    def delete_category_rule(self, id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from regras_categorizacao where id = %s", (id,))

    # --- ORÇAMENTOS ---
    def get_budgets(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("select * from orcamentos order by categoria")
                return [dict(row) for row in cur.fetchall()]

    def set_budget(self, categoria, valor_limite):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into orcamentos (categoria, valor_limite)
                    values (%s, %s)
                    on conflict (categoria) do update set valor_limite = excluded.valor_limite
                    """,
                    (categoria, valor_limite),
                )

    def delete_budget(self, categoria):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from orcamentos where categoria = %s", (categoria,))

    # --- CONTAS A VENCER ---
    def get_upcoming_bills(self, days: int = 7):
        """Transações com data_vencimento entre hoje e hoje+days (inclusive)."""
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select * from transacoes
                    where data_vencimento is not null
                      and data_vencimento between current_date and (current_date + (%s || ' days')::interval)
                    order by data_vencimento asc
                    """,
                    (days,),
                )
                return [dict(row) for row in cur.fetchall()]

    # --- DASHBOARD ---
    def get_dashboard_data(self, month: str = None):
        """Retorna dados agregados para os gráficos.

        month: filtro opcional no formato "YYYY-MM". Quando definido, os
        cards de métricas, o gráfico de despesas por categoria e o cálculo
        de orçamentos passam a refletir apenas aquele mês. "Receita x
        Despesa por Mês" e "Evolução dos Investimentos" continuam mostrando
        a série histórica completa - são visões multi-mês por natureza.
        """
        transactions = self.get_transactions()
        if not transactions:
            orcamentos_vazios = [
                {"categoria": b["categoria"], "limite": float(b["valor_limite"]), "gasto": 0.0, "percentual": 0.0, "estourado": False}
                for b in self.get_budgets()
            ]
            return {
                "expenses_by_category": [], "investments_evolution": [], "monthly_evolution": [],
                "orcamentos": orcamentos_vazios, "contas_a_vencer": [],
            }

        def _mes_da_transacao(t):
            data_t = t["data"]
            return f"{data_t.year:04d}-{data_t.month:02d}" if hasattr(data_t, "year") else str(data_t)[:7]

        # Transações do mês selecionado (ou todas, se nenhum mês for informado).
        # Usado nas métricas e no gráfico de despesas por categoria - os
        # gráficos históricos (evolução mensal/investimentos) usam sempre
        # `transactions` completo.
        filtradas = [t for t in transactions if _mes_da_transacao(t) == month] if month else transactions

        # 1. Despesas por Categoria (exclui Investimentos - aporte é saída de
        # caixa, não "gasto de consumo", e já tem seu próprio gráfico de
        # evolução; incluir aqui dominava e distorcia o gráfico de pizza)
        expenses = {}
        for t in filtradas:
            if t["tipo"] == "Despesa" and t["categoria"] != "Investimentos":
                cat = t["categoria"] or "Outros"
                expenses[cat] = expenses.get(cat, 0) + float(t["valor"])

        pie_data = [{"name": k, "value": abs(v)} for k, v in expenses.items()]

        # 2. Evolução Investimentos (Acumulado) - agregado por dia. Várias
        # transações no mesmo dia (comum em aplicações automáticas) geravam
        # um "sub-degrau" cada uma; agregando por dia a curva reflete o saldo
        # real ao final de cada dia, bem mais legível.
        investments = [t for t in transactions if t["categoria"] == "Investimentos" or t["tipo"] == "Investimento"]

        daily_deltas: dict = {}
        for t in investments:
            val = float(t["valor"])
            delta = abs(val) if t["tipo"] == "Despesa" else -val
            data_t = t["data"]
            data_key = data_t.isoformat() if hasattr(data_t, "isoformat") else data_t
            daily_deltas[data_key] = daily_deltas.get(data_key, 0) + delta

        evolution_data = []
        accumulated = 0
        for data_key in sorted(daily_deltas.keys()):
            accumulated += daily_deltas[data_key]
            evolution_data.append({"data": data_key, "valor": accumulated})

        # 3. Evolução mensal: Receita vs Despesa (exclui Investimentos)
        monthly: dict = {}
        for t in transactions:
            if t["categoria"] == "Investimentos" or t["tipo"] == "Investimento":
                continue
            data_t = t["data"]
            chave_mes = f"{data_t.year:04d}-{data_t.month:02d}" if hasattr(data_t, "year") else str(data_t)[:7]
            bucket = monthly.setdefault(chave_mes, {"receita": 0.0, "despesa": 0.0})
            if t["tipo"] == "Receita":
                bucket["receita"] += float(t["valor"])
            elif t["tipo"] == "Despesa":
                bucket["despesa"] += abs(float(t["valor"]))

        monthly_evolution = [
            {"mes": mes, "receita": v["receita"], "despesa": v["despesa"]}
            for mes, v in sorted(monthly.items())
        ]

        # 4. Orçamentos: gasto do mês de referência por categoria vs. limite
        # definido. Usa o mês selecionado no filtro, ou o mês corrente quando
        # nenhum filtro foi aplicado.
        if month:
            ano_ref, mes_ref = int(month[:4]), int(month[5:7])
        else:
            hoje = datetime.now(timezone.utc).date()
            ano_ref, mes_ref = hoje.year, hoje.month

        gastos_mes_atual: dict = {}
        for t in transactions:
            if t["tipo"] != "Despesa":
                continue
            data_t = t["data"]
            if hasattr(data_t, "year"):
                ano_t, mes_t = data_t.year, data_t.month
            else:
                try:
                    ano_t, mes_t = int(str(data_t)[:4]), int(str(data_t)[5:7])
                except (ValueError, IndexError):
                    continue
            if ano_t == ano_ref and mes_t == mes_ref:
                cat = t["categoria"] or "Outros"
                gastos_mes_atual[cat] = gastos_mes_atual.get(cat, 0) + abs(float(t["valor"]))

        orcamentos_status = []
        for b in self.get_budgets():
            cat = b["categoria"]
            limite = float(b["valor_limite"])
            gasto = gastos_mes_atual.get(cat, 0.0)
            orcamentos_status.append({
                "categoria": cat,
                "limite": limite,
                "gasto": gasto,
                "percentual": round((gasto / limite * 100), 1) if limite > 0 else 0.0,
                "estourado": gasto > limite,
            })

        contas_a_vencer = [
            {
                "id": c["id"],
                "descricao": c["descricao"],
                "valor": abs(float(c["valor"])),
                "categoria": c["categoria"],
                "data_vencimento": c["data_vencimento"].isoformat() if hasattr(c["data_vencimento"], "isoformat") else c["data_vencimento"],
            }
            for c in self.get_upcoming_bills(7)
        ]

        return {
            "expenses_by_category": pie_data,
            "investments_evolution": evolution_data,
            "monthly_evolution": monthly_evolution,
            "orcamentos": orcamentos_status,
            "contas_a_vencer": contas_a_vencer,
            "metrics": {
                "receitas": sum(float(t["valor"]) for t in filtradas if t["tipo"] == "Receita" and t["categoria"] != "Investimentos" and t["tipo"] != "Investimento"),
                "despesas": sum(abs(float(t["valor"])) for t in filtradas if t["tipo"] == "Despesa" and t["categoria"] != "Investimentos"),
                "investido": accumulated,
                "saldo": sum(float(t["valor"]) for t in filtradas if t["categoria"] != "Investimentos" and t["tipo"] != "Investimento"),
            },
        }
