import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class DatabaseManager:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("Aviso: SUPABASE_URL ou SUPABASE_KEY não definidos.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)

    def save_transactions(self, transactions: list):
        """Salva uma lista de transações no Supabase"""
        if not self.client:
            return {"error": "Banco de dados não configurado"}
            
        try:
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
            
            response = self.client.table("transacoes").insert(data_to_insert).execute()
            return response
        except Exception as e:
            raise Exception(f"Erro ao salvar no banco: {str(e)}")

    def get_transactions(self):
        """Busca todas as transações"""
        if not self.client:
            return []
        try:
            response = self.client.table("transacoes").select("*").order("data", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar transações: {e}")
            return []

    # --- CATEGORIAS ---
    def get_categories(self):
        if not self.client: return []
        try:
            return self.client.table("categorias").select("*").execute().data
        except: return []

    def add_category(self, nome, tipo):
        if not self.client: return None
        try:
            return self.client.table("categorias").insert({"nome": nome, "tipo": tipo}).execute()
        except Exception as e:
            raise e

    def delete_category(self, id):
        if not self.client: return None
        try:
            return self.client.table("categorias").delete().eq("id", id).execute()
        except: return None

    def update_category(self, id, nome, tipo):
        if not self.client: return None
        try:
            return self.client.table("categorias").update({"nome": nome, "tipo": tipo}).eq("id", id).execute()
        except: return None

    def add_manual_transaction(self, t):
        if not self.client: return None
        try:
            # Convert date if needed, or assume backend receives YYYY-MM-DD
            return self.client.table("transacoes").insert({
                "data": t["data"],
                "descricao": t["descricao"],
                "valor": t["valor"],
                "categoria": t["categoria"],
                "tipo": t["tipo"],
                "fonte": "Manual",
                "data_vencimento": t.get("data_vencimento")
            }).execute()
        except Exception as e:
            raise e

    def delete_transaction(self, id):
        if not self.client: return None
        try:
            return self.client.table("transacoes").delete().eq("id", id).execute()
        except: return None

    def delete_all_transactions(self):
        if not self.client: return None
        try:
            # Delete all rows where id is not null (effectively all)
            return self.client.table("transacoes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception as e:
            print(f"Erro ao deletar tudo: {e}")
            return None

    def update_transaction(self, id, data):
        if not self.client: return None
        try:
            # data is a dict with fields to update (e.g., {"categoria": "Nova"})
            return self.client.table("transacoes").update(data).eq("id", id).execute()
        except: return None

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
