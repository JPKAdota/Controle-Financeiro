import pandas as pd
from datetime import datetime
import re
import pdfplumber
import io

class ProcessadorExtratos:
    def __init__(self):
        self.categorias_padrao = {
            'Comida': ['supermercado', 'mercado', 'padaria', 'restaurante', 'lanchonete', 'ifood', 'rappi', 'hamburguer', 'pizza', 'delivery'],
            'Transporte': ['uber', '99', 'taxi', 'combustível', 'posto', 'estacionamento', 'metro', 'onibus', 'bilhete', 'passagem', 'pedágio'],
            'Moradia': ['aluguel', 'condomínio', 'luz', 'água', 'energia', 'internet', 'telefone', 'gás', 'energia', 'eletropaulo', 'sabesp'],
            'Lazer': ['cinema', 'netflix', 'spotify', 'shopping', 'parque', 'viagem', 'hotel', 'show', 'teatro', 'musical'],
            'Saúde': ['farmacia', 'drogaria', 'médico', 'hospital', 'plano de saúde', 'academia', 'clinica', 'dentista'],
            'Educação': ['escola', 'faculdade', 'curso', 'livraria', 'material escolar', 'universidade', 'mensalidade'],
            'Investimentos': ['rendimento', 'dividendo', 'aplicação', 'tesouro', 'ação', 'fii', 'investimento', 'cdb', 'lci'],
            'Receita': ['salário', 'pagamento', 'transferência recebida', 'depósito', 'rendimento']
        }
    
    def categorizar_transacao(self, descricao, valor):
        """Categoriza automaticamente uma transação baseada na descrição"""
        desc_lower = descricao.lower()
        
        for categoria, palavras_chave in self.categorias_padrao.items():
            for palavra in palavras_chave:
                if palavra in desc_lower:
                    return categoria
        
        return "A Categorizar"
    
    def extrair_texto_pdf(self, arquivo_bytes):
        """Extrai texto de um PDF"""
        try:
            texto_completo = ""
            with pdfplumber.open(io.BytesIO(arquivo_bytes)) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo += texto + "\n"
            return texto_completo
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def parsear_transacoes_pdf(self, texto):
        """Parseia transações de texto de PDF bancário"""
        transacoes = []
        linhas = texto.split('\n')
        
        regex_linha = r'^(\d{2}/\d{2}(?:/\d{4})?)\s+(.*?)\s+(-?[\d.]+(?:,\d{2})?)$'
        
        for linha in linhas:
            linha = linha.strip()
            match = re.search(regex_linha, linha)
            
            if match:
                data_str = match.group(1)
                descricao = match.group(2).strip()
                valor_str = match.group(3)
                
                if len(data_str) == 5: 
                    ano_atual = datetime.now().year
                    mes = int(data_str.split('/')[1])
                    if mes > datetime.now().month:
                        ano = ano_atual - 1
                    else:
                        ano = ano_atual
                    data_str = f"{data_str}/{ano}"
                
                try:
                    valor_limpo = valor_str.replace('.', '').replace(',', '.')
                    valor = float(valor_limpo)
                    descricao = re.sub(r'\d{2}/\d{2}$', '', descricao).strip()
                    
                    if "SALDO" in descricao.upper():
                        continue
                    
                    categoria = self.categorizar_transacao(descricao, valor)
                    
                    transacao = {
                        'data': data_str,
                        'descricao': descricao,
                        'valor': valor,
                        'categoria': categoria,
                        'tipo': 'Receita' if valor > 0 else 'Despesa',
                        'fonte': 'PDF'
                    }
                    transacoes.append(transacao)
                    
                except Exception:
                    continue
                    
        return transacoes
    
    def processar_pdf(self, arquivo_bytes):
        """Processa um arquivo PDF (bytes)"""
        try:
            texto = self.extrair_texto_pdf(arquivo_bytes)
            if not texto:
                raise Exception("Não foi possível extrair texto do PDF")
            
            transacoes = self.parsear_transacoes_pdf(texto)
            if not transacoes:
                raise Exception("Não foi possível identificar transações no PDF")
            
            return transacoes # Retorna lista de dicts
            
        except Exception as e:
            raise Exception(f"Erro ao processar PDF: {str(e)}")
    
    def processar_csv(self, arquivo_bytes):
        """Processa um arquivo CSV (bytes)"""
        try:
            df = pd.read_csv(io.BytesIO(arquivo_bytes))
            df.columns = [col.lower().strip() for col in df.columns]
            
            colunas_necessarias = ['data', 'descrição', 'valor']
            
            # Normalização de colunas
            # (Simplificando para a versão API, assumindo que o pandas resolve a leitura direta se o formato estiver ok)
            # Mas vamos manter a lógica de renomear para garantir
            
            renames = {}
            for col in df.columns:
                if 'descrição' in col or 'descricao' in col: renames[col] = 'descricao'
                if 'data' in col: renames[col] = 'data'
                if 'valor' in col: renames[col] = 'valor'
            
            df = df.rename(columns=renames)
            
            if not all(col in df.columns for col in ['data', 'descricao', 'valor']):
                raise Exception("CSV não possui colunas necessárias (Data, Descrição, Valor)")
            
            transacoes = []
            for _, row in df.iterrows():
                try:
                    descricao = str(row['descricao']).strip()
                    val_str = str(row['valor']).replace('R$', '').replace(',', '.').strip()
                    valor = float(val_str)
                    data = str(row['data'])
                    
                    categoria = self.categorizar_transacao(descricao, valor)
                    
                    transacoes.append({
                        'data': data,
                        'descricao': descricao,
                        'valor': valor,
                        'categoria': categoria,
                        'tipo': 'Receita' if valor > 0 else 'Despesa',
                        'fonte': 'CSV'
                    })
                except:
                    continue
            
            return transacoes

        except Exception as e:
            raise Exception(f"Erro ao processar CSV: {str(e)}")
