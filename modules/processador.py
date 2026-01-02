import pandas as pd
import streamlit as st
from datetime import datetime
import re
import pdfplumber  # ← NOVO: Para PDFs
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
        
        # Se não encontrou, classifica como "A Categorizar" para revisão manual
        return "A Categorizar"
    
    def extrair_texto_pdf(self, arquivo_pdf):
        """Extrai texto de um PDF"""
        try:
            texto_completo = ""
            with pdfplumber.open(arquivo_pdf) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo += texto + "\n"
            return texto_completo
        except Exception as e:
            st.error(f"❌ Erro ao extrair texto do PDF: {e}")
            return ""
    
    def parsear_transacoes_pdf(self, texto):
        """Parseia transações de texto de PDF bancário"""
        transacoes = []
        linhas = texto.split('\n')
        
        # Padrão: DATA DESCRIÇÃO VALOR
        # Ex: 11/12/2025 PIX QRS CEN -49,13
        # Ex: 11/12 INTRO AUTO11/12 -49,13 (as vezes a data repete ou tem lixo)
        
        # Regex captura: (Data) ... (Descrição) ... (Valor)
        regex_linha = r'^(\d{2}/\d{2}(?:/\d{4})?)\s+(.*?)\s+(-?[\d.]+(?:,\d{2})?)$'
        
        for linha in linhas:
            linha = linha.strip()
            
            # Tenta dar match na linha inteira primeiro
            match = re.search(regex_linha, linha)
            
            if match:
                data_str = match.group(1)
                descricao = match.group(2).strip()
                valor_str = match.group(3)
                
                # Se a data não tiver ano, tenta inferir (assumindo ano atual ou anterior)
                if len(data_str) == 5: # dd/mm
                    ano_atual = datetime.now().year
                    # Se o mês for maior que o atual, provavelmente é ano passado
                    mes = int(data_str.split('/')[1])
                    if mes > datetime.now().month:
                        ano = ano_atual - 1
                    else:
                        ano = ano_atual
                    data_str = f"{data_str}/{ano}"
                
                try:
                    # Limpa formato do valor (1.000,00 -> 1000.00)
                    valor_limpo = valor_str.replace('.', '').replace(',', '.')
                    valor = float(valor_limpo)
                    
                    # Remove datas extras que as vezes aparecem na descrição
                    # Ex: "DESCRIÇÃO 11/12"
                    descricao = re.sub(r'\d{2}/\d{2}$', '', descricao).strip()
                    
                    # IGNORAR LINHAS DE SALDO
                    # "SALDO DO DIA", "SALDO APLIC AUT", etc não são transações reais de entrada/saída
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
                    
                except Exception as e:
                    # Se falhar conversão, pula
                    continue
                    
        return transacoes
    
    def processar_pdf(self, arquivo_pdf):
        """Processa um arquivo PDF de extrato bancário"""
        try:
            # Extrai texto do PDF
            texto = self.extrair_texto_pdf(arquivo_pdf)
            
            if not texto:
                st.error("❌ Não foi possível extrair texto do PDF")
                return None
            
            # Parseia transações
            transacoes = self.parsear_transacoes_pdf(texto)
            
            if not transacoes:
                st.error("❌ Não foi possível identificar transações no PDF")
                return None
            
            st.success(f"✅ Extraídas {len(transacoes)} transações do PDF")
            
            # Mostra preview do texto extraído (útil para debug)
            with st.expander("🔍 Visualizar texto extraído do PDF"):
                st.text_area("Texto extraído:", texto[:2000] + "..." if len(texto) > 2000 else texto, height=200)
            
            return pd.DataFrame(transacoes)
            
        except Exception as e:
            st.error(f"❌ Erro ao processar PDF: {str(e)}")
            return None
    
    def processar_csv(self, arquivo_csv):
        """Processa um arquivo CSV de extrato bancário"""
        try:
            # Lê o CSV
            df = pd.read_csv(arquivo_csv)
            
            # Log para debug
            st.write("📊 Colunas encontradas no CSV:", df.columns.tolist())
            
            # Padroniza nomes das colunas
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Verifica colunas necessárias
            colunas_necessarias = ['data', 'descrição', 'valor']
            colunas_encontradas = []
            
            for col in colunas_necessarias:
                if col in df.columns:
                    colunas_encontradas.append(col)
                else:
                    # Tenta encontrar colunas similares
                    for col_df in df.columns:
                        if col in col_df or col_df in col:
                            df = df.rename(columns={col_df: col})
                            colunas_encontradas.append(col)
                            break
            
            if len(colunas_encontradas) < 2:
                st.error("❌ CSV não possui colunas necessárias. Esperado: 'Data', 'Descrição', 'Valor'")
                return None
            
            # Processa as transações
            transacoes_processadas = []
            
            for index, row in df.iterrows():
                try:
                    descricao = str(row.get('descrição', row.get('descricao', ''))).strip()
                    valor_str = str(row.get('valor', '0')).replace('R$', '').replace(',', '.').strip()
                    
                    # Converte valor para float
                    try:
                        valor = float(valor_str)
                    except:
                        valor = 0.0
                    
                    # Data
                    data_str = str(row.get('data', ''))
                    
                    # Categoriza
                    categoria = self.categorizar_transacao(descricao, valor)
                    
                    transacao = {
                        'data': data_str,
                        'descricao': descricao,
                        'valor': valor,
                        'categoria': categoria,
                        'tipo': 'Receita' if valor > 0 else 'Despesa',
                        'fonte': 'CSV'
                    }
                    
                    transacoes_processadas.append(transacao)
                    
                except Exception as e:
                    continue
            
            return pd.DataFrame(transacoes_processadas)
            
        except Exception as e:
            st.error(f"❌ Erro ao processar CSV: {str(e)}")
            return None
    
    def processar_arquivo(self, arquivo):
        """Processa qualquer tipo de arquivo (CSV ou PDF)"""
        if arquivo.type == "text/csv":
            return self.processar_csv(arquivo)
        elif arquivo.type == "application/pdf":
            return self.processar_pdf(arquivo)
        else:
            st.error(f"❌ Formato não suportado: {arquivo.type}")
            return None
    
    def calcular_metricas(self, df_transacoes):
        """Calcula métricas financeiras baseadas nas transações"""
        if df_transacoes is None or df_transacoes.empty:
            return None
        
        # Filtra transações
        transacoes_invest = df_transacoes[df_transacoes['categoria'] == 'Investimentos']
        transacoes_comuns = df_transacoes[df_transacoes['categoria'] != 'Investimentos']
        
        # Receitas e Despesas (Operacionais - Sem Investimentos)
        receitas_op = transacoes_comuns[transacoes_comuns['tipo'] == 'Receita']['valor'].sum()
        despesas_op = transacoes_comuns[transacoes_comuns['tipo'] == 'Despesa']['valor'].sum()
        
        # Fluxo de Investimentos
        # Aplicação = Dinheiro saindo da conta (-), mas é positivo para o patrimônio
        aplicacoes = transacoes_invest[transacoes_invest['tipo'] == 'Despesa']['valor'].sum()
        # Resgate = Dinheiro entrando (+), mas não é renda nova
        resgates = transacoes_invest[transacoes_invest['tipo'] == 'Receita']['valor'].sum()
        
        # Saldo Líquido da Conta (Esse considera TUDO: Salário - Gastos - Investimentos)
        saldo_conta = df_transacoes['valor'].sum()
        
        # Taxa de Poupança: (Saldo Operacional + Aplicações) / Receita Operacional
        # Quanto do que eu ganhei (Salário) eu não gastei (Sobrou na conta ou Investi)
        sobra_operacional = receitas_op - abs(despesas_op)
        
        try:
            taxa_poupanca = ((sobra_operacional) / receitas_op * 100) if receitas_op > 0 else 0
        except:
            taxa_poupanca = 0
            
        metricas = {
            'receitas_total': receitas_op,       # Apenas ganhos reais (Salário, etc)
            'despesas_total': abs(despesas_op),  # Apenas gastos reais (Mercado, Luz...)
            'saldo': saldo_conta,                # Saldo final da conta corrente
            'investimentos_total': abs(aplicacoes), # Quanto eu investi esse mês
            'investimentos_resgates': resgates,
            'taxa_poupanca': taxa_poupanca,
            'total_transacoes': len(df_transacoes)
        }
        
        return metricas