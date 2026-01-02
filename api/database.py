import os
from supabase import create_client, Client

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
