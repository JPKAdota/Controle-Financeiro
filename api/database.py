import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class DatabaseError(RuntimeError):
    """Erro operacional ao acessar o banco de dados."""


class DatabaseManager:
    def __init__(self, access_token: str | None = None):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            self.client = None
        else:
            try:
                self.client: Client | None = create_client(url, key)
                if access_token and self.client:
                    self.client.postgrest.auth(access_token)
            except Exception as exc:
                raise DatabaseError("Não foi possível conectar ao banco de dados.") from exc

    def _require_client(self) -> Client:
        if not self.client:
            raise DatabaseError("Banco de dados não configurado.")
        return self.client

    def save_transactions(self, transactions: list):
        """Salva uma lista de transações no Supabase"""
        try:
            client = self._require_client()
            # Prepara dados para inserção (garante que chaves batam com colunas do DB)
            data_to_insert = []
            for t in transactions:
                # Converte data DD/MM/YYYY para YYYY-MM-DD para o Postgres
                try:
                    parts = t['data'].split('/')
                    if len(parts) == 3:
                        iso_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    else:
                        iso_date = t['data']
                except:
                    iso_date = t['data']

                data_to_insert.append({
                    "data": iso_date,
                    "descricao": t['descricao'],
                    "valor": t['valor'],
                    "categoria": t['categoria'],
                    "tipo": t['tipo'],
                    "fonte": t['fonte']
                })
            
            response = client.table("transacoes").insert(data_to_insert).execute()
            return response
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao salvar transações no banco de dados.") from exc

    def get_transactions(self):
        """Busca todas as transações"""
        try:
            response = self._require_client().table("transacoes").select("*").order("data", desc=True).execute()
            return response.data
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao buscar transações.") from exc

    # --- CATEGORIAS ---
    def get_categories(self):
        try:
            return self._require_client().table("categorias").select("*").execute().data
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao buscar categorias.") from exc

    def add_category(self, nome, tipo):
        try:
            return self._require_client().table("categorias").insert({"nome": nome, "tipo": tipo}).execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao adicionar categoria.") from exc

    def delete_category(self, id):
        try:
            return self._require_client().table("categorias").delete().eq("id", id).execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao remover categoria.") from exc

    def update_category(self, id, nome, tipo):
        try:
            return self._require_client().table("categorias").update({"nome": nome, "tipo": tipo}).eq("id", id).execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao atualizar categoria.") from exc

    def add_manual_transaction(self, t):
        try:
            # Convert date if needed, or assume backend receives YYYY-MM-DD
            return self._require_client().table("transacoes").insert({
                "data": t["data"],
                "descricao": t["descricao"],
                "valor": t["valor"],
                "categoria": t["categoria"],
                "tipo": t["tipo"],
                "fonte": "Manual",
                "data_vencimento": t.get("data_vencimento")
            }).execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao adicionar transação.") from exc

    def delete_transaction(self, id):
        try:
            return self._require_client().table("transacoes").delete().eq("id", id).execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao remover transação.") from exc

    def delete_all_transactions(self):
        try:
            # Delete all rows where id is not null (effectively all)
            return self._require_client().table("transacoes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao remover transações.") from exc

    def update_transaction(self, id, data):
        try:
            # data is a dict with fields to update (e.g., {"categoria": "Nova"})
            return self._require_client().table("transacoes").update(data).eq("id", id).execute()
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError("Erro ao atualizar transação.") from exc

    # --- DASHBOARD ---
    def get_dashboard_data(self):
        """Retorna dados agregados para os gráficos"""
        transactions = self.get_transactions()
        if not transactions:
            return {"expenses_by_category": [], "investments_evolution": []}
        
        # 1. Despesas por Categoria
        expenses = {}
        for t in transactions:
            if t['tipo'] == 'Despesa':
                cat = t['categoria'] or 'Outros'
                expenses[cat] = expenses.get(cat, 0) + float(t['valor'])
        
        pie_data = [{"name": k, "value": abs(v)} for k, v in expenses.items()]

        # 2. Evolução Investimentos (Acumulado)
        # Filtra investimentos
        investments = [t for t in transactions if t['categoria'] == 'Investimentos' or t['tipo'] == 'Investimento']
        # Ordena por data crescente
        investments.sort(key=lambda x: x['data'])
        
        evolution_data = []
        accumulated = 0
        for t in investments:
            # Se for 'Despesa' no contexto de investimento, é aporte (+)
            # Se for 'Receita', é resgate (-)
            # Mas verifique como o processador classifica. 
            # Geralmente: Saiu da conta (Despesa) -> Entrou no Investimento (+)
            val = float(t['valor'])
            if t['tipo'] == 'Despesa':
                accumulated += abs(val)
            else:
                accumulated -= val # Resgate diminui o saldo investido
            
            evolution_data.append({
                "data": t['data'],
                "valor": accumulated
            })

        return {
            "expenses_by_category": pie_data,
            "investments_evolution": evolution_data,
            "metrics": {
                "receitas": sum(float(t['valor']) for t in transactions if t['tipo'] == 'Receita' and t['categoria'] != 'Investimentos' and t['tipo'] != 'Investimento'),
                "despesas": sum(abs(float(t['valor'])) for t in transactions if t['tipo'] == 'Despesa' and t['categoria'] != 'Investimentos'),
                "investido": accumulated, # Total acumulado final
                "saldo": sum(float(t['valor']) for t in transactions if t['categoria'] != 'Investimentos' and t['tipo'] != 'Investimento')
                # Nota: Saldo geralmente não conta investimentos como 'gasto', mas aporte sai da conta.
                # Se quisermos saldo da CONTA CORRENTE, tudo conta.
                # Se quisermos saldo CONTÁBIL (Patrimônio), investimento é ativo.
                # Vamos simplificar: Saldo = Receitas - Despesas (sem contar investimento como despesa de 'perda', mas sai do caixa)
                # Na verdade, a regra anterior era: Saldo = Soma de tudo (investimento é negativo pois sai da conta).
            }
        }
