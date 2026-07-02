import pandas as pd
from datetime import datetime
import re
import pdfplumber
import PyPDF2
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
        """Extrai texto de um PDF usando pdfplumber ou PyPDF2 fallback"""
        import warnings
        texto_pdfplumber = ""
        
        # 1. Tenta com pdfplumber (suprimindo warnings de fonte)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with pdfplumber.open(io.BytesIO(arquivo_bytes)) as pdf:
                    for pagina in pdf.pages:
                        try:
                            texto = pagina.extract_text()
                            if texto:
                                texto_pdfplumber += texto + "\n"
                        except Exception:
                            continue  # Pula páginas problemáticas
        except Exception as e:
            print(f"Aviso: pdfplumber falhou completamente ({e})")
        
        # 2. Se pdfplumber conseguiu texto útil, retorna
        if len(texto_pdfplumber.strip()) > 20:
            print(f"pdfplumber extraiu {len(texto_pdfplumber)} caracteres")
            return texto_pdfplumber
        
        # 3. Fallback: PyPDF2 (mais tolerante com fontes problemáticas como Neon)
        print("pdfplumber não extraiu texto suficiente, tentando PyPDF2...")
        texto_pypdf2 = ""
        try:
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo_bytes))
            for pagina in leitor.pages:
                try:
                    texto = pagina.extract_text()
                    if texto:
                        texto_pypdf2 += texto + "\n"
                except Exception:
                    continue
        except Exception as e:
            print(f"Erro no fallback PyPDF2: {e}")
        
        print(f"PyPDF2 extraiu {len(texto_pypdf2)} caracteres")
        return texto_pypdf2
    
    def parsear_transacoes_pdf(self, texto):
        """Parseia transações de texto de PDF bancário cruzando lógicas flexíveis"""
        transacoes = []
        
        # Detecta se é fatura de cartão de crédito
        texto_upper = texto.upper()
        eh_fatura = any(termo in texto_upper for termo in [
            "LIMITES DE CRÉDITO", "LIMITE DE CRÉDITO", "LIMITE TOTAL DE CRÉDITO", 
            "RESUMO DA FATURA", "TOTAL DESTA FATURA", "TOTAL DA FATURA", 
            "LANÇAMENTOS: COMPRAS E SAQUES", "COMPRAS E SAQUES", "PAGAMENTO MÍNIMO",
            "ENCARGOS COBRADOS NESTA FATURA"
        ])
        if eh_fatura:
            print("Detectado formato de fatura de cartão de crédito. Ajustando sinais...")
            
        # Limpa caracteres nulos (o Neon usa \x00 como separador em vários lugares)
        # Substitui \x00 por espaço para normalizar, MAS preserva o padrão de negativo
        # No Neon, negativo aparece como "\x00R$" (null antes do R$)
        # Primeiro marca os negativos, depois limpa os nulls
        texto_limpo = texto.replace('\x00R$', '-R$')  # Marca negativos do Neon
        texto_limpo = texto_limpo.replace('\x00', ' ')  # Limpa nulls restantes (ex: hora)
        
        linhas = texto_limpo.split('\n')
        
        # Regex para formato Neon: DESCRIÇÃO DD/MM/YYYY HH:MM [-]R$ VALOR R$ SALDO CARTÃO
        # Exemplo: "TED recebido de TECH4HUMANS... 06/02/2026 07 35 R$ 3.325,89 R$ 3.325,89 -"
        # Exemplo negativo: "PIX enviado para NATALIA... 06/02/2026 10 37 -R$ 3.325,89 R$ 0,00 -"
        regex_neon = r'^(.+?)\s+(\d{2}/\d{2}/\d{4})\s+\d{2}\s*\d{2}\s+(-?)R\$\s*([\d.,]+)\s+R\$\s*[\d.,]+\s+-$'
        
        # Regex genérica (outros bancos): DATA DESCRIÇÃO VALOR
        regex_generica = r'(?:^|\s)(\d{2}[/-]\d{2}(?:[/-]\d{2,4})?)\s+(.*?)\s+(?:R\$?\s*)?(-?\s*[\d.]+(?:,\d{2})?)$'
        
        for linha in linhas:
            linha = linha.strip()
            if not linha or len(linha) < 10:
                continue
            
            # Tenta Neon primeiro
            match_neon = re.search(regex_neon, linha)
            if match_neon:
                descricao = match_neon.group(1).strip()
                data_str = match_neon.group(2)
                sinal_negativo = match_neon.group(3)  # "-" ou ""
                valor_str = match_neon.group(4)
                
                try:
                    valor_limpo = valor_str.replace('.', '').replace(',', '.')
                    valor = float(valor_limpo)
                    
                    if sinal_negativo == '-':
                        valor = -abs(valor)
                    
                    # Se for fatura de cartão, inverte o sinal do valor:
                    # Compras (positivo na fatura) viram débito (-) e pagamentos (negativo) viram crédito (+)
                    if eh_fatura:
                        valor = -valor
                    
                    # Pula linhas de cabeçalho/saldo/lixo
                    if "SALDO" in descricao.upper() or valor == 0:
                        continue
                    if len(descricao) < 5 or descricao.replace(' ', '').isdigit():
                        continue  # Pula descrições muito curtas ou só números (cabeçalho)
                    
                    categoria = self.categorizar_transacao(descricao, valor)
                    
                    transacoes.append({
                        'data': data_str,
                        'descricao': descricao,
                        'valor': valor,
                        'categoria': categoria,
                        'tipo': 'Receita' if valor > 0 else 'Despesa',
                        'fonte': 'PDF'
                    })
                except Exception:
                    continue
                continue  # Já achou match Neon, pula pro próximo
            
            # Fallback: regex genérica (outros bancos)
            match_gen = re.search(regex_generica, linha)
            if match_gen:
                data_str = match_gen.group(1).replace('-', '/')
                descricao = match_gen.group(2).strip()
                valor_str = match_gen.group(3)
                
                if len(data_str) == 5:
                    ano_atual = datetime.now().year
                    mes = int(data_str.split('/')[1])
                    if mes > datetime.now().month:
                        ano = ano_atual - 1
                    else:
                        ano = ano_atual
                    data_str = f"{data_str}/{ano}"
                
                try:
                    valor_str = valor_str.replace(' ', '')
                    valor_limpo = valor_str.replace('.', '').replace(',', '.')
                    valor = float(valor_limpo)
                    
                    # Se for fatura de cartão, inverte o sinal do valor
                    if eh_fatura:
                        valor = -valor
                    
                    descricao = re.sub(r'\d{2}/\d{2}$', '', descricao).strip()
                    
                    if "SALDO" in descricao.upper():
                        continue
                    if len(descricao) < 5 or descricao.replace(' ', '').isdigit():
                        continue  # Pula descrições curtas ou só números (cabeçalho)
                    
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
                # Retorna algumas linhas do PDF para debug se a regex falhar em tudo
                linhas_validas = [l.strip() for l in texto.split('\n') if len(l.strip()) > 5]
                amostra = " | ".join(linhas_validas[:5])
                raise Exception(f"Não foi possível identificar transações no PDF. Formato do texto extraído: {amostra}")
            
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
