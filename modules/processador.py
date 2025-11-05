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
        
        # Se não encontrou, classifica como "Outros" ou pela natureza do valor
        if valor > 0:
            return "Receita"
        else:
            return "Outras Despesas"
    
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
        
        # Padrões comuns em extratos bancários
        padrao_data = r'(\d{2}/\d{2}/\d{4}|\d{2}/\d{2})'
        padrao_valor = r'R\$\s*([\d.,]+)'
        padrao_valor_simples = r'([\d.,]+)'
        
        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            
            # Tenta encontrar uma data no início da linha
            match_data = re.search(padrao_data, linha)
            if match_data:
                data = match_data.group(1)
                
                # A descrição geralmente vem depois da data
                partes = linha.split()
                descricao_parts = []
                valor_encontrado = None
                
                # Procura pela descrição e valor
                for parte in partes[1:]:  # Pula a data
                    # Verifica se é um valor
                    if re.search(padrao_valor, parte) or (re.search(padrao_valor_simples, parte) and len(parte) > 5):
                        # Provavelmente é um valor
                        valor_str = parte.replace('R$', '').replace('.', '').replace(',', '.')
                        try:
                            valor = float(valor_str)
                            valor_encontrado = valor
                            break
                        except:
                            descricao_parts.append(parte)
                    else:
                        descricao_parts.append(parte)
                
                descricao = ' '.join(descricao_parts)
                
                # Se não encontrou valor nesta linha, tenta na próxima
                if valor_encontrado is None and i + 1 < len(linhas):
                    proxima_linha = linhas[i + 1].strip()
                    match_valor = re.search(padrao_valor, proxima_linha)
                    if match_valor:
                        valor_str = match_valor.group(1).replace('.', '').replace(',', '.')
                        try:
                            valor_encontrado = float(valor_str)
                            i += 1  # Pula a próxima linha
                        except:
                            pass
                
                if valor_encontrado is not None and descricao:
                    # Determina se é débito ou crédito (simplificado)
                    # Em PDFs, geralmente valores negativos têm indicação ou estão em seções diferentes
                    # Vamos considerar negativo por padrão para despesas
                    if any(palavra in descricao.lower() for palavra in ['pagamento', 'compra', 'debito', 'tarifa']):
                        valor_encontrado = -abs(valor_encontrado)
                    elif any(palavra in descricao.lower() for palavra in ['deposito', 'credito', 'salario', 'rendimento']):
                        valor_encontrado = abs(valor_encontrado)
                    else:
                        # Se não conseguiu determinar, assume negativo (mais comum em extratos)
                        valor_encontrado = -abs(valor_encontrado)
                    
                    categoria = self.categorizar_transacao(descricao, valor_encontrado)
                    
                    transacao = {
                        'data': data,
                        'descricao': descricao,
                        'valor': valor_encontrado,
                        'categoria': categoria,
                        'tipo': 'Receita' if valor_encontrado > 0 else 'Despesa',
                        'fonte': 'PDF'
                    }
                    
                    transacoes.append(transacao)
            
            i += 1
        
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
        
        receitas = df_transacoes[df_transacoes['tipo'] == 'Receita']['valor'].sum()
        despesas = df_transacoes[df_transacoes['tipo'] == 'Despesa']['valor'].sum()
        saldo = receitas - abs(despesas)
        
        metricas = {
            'receitas_total': receitas,
            'despesas_total': abs(despesas),
            'saldo': saldo,
            'taxa_poupanca': (saldo / receitas * 100) if receitas > 0 else 0,
            'total_transacoes': len(df_transacoes)
        }
        
        return metricas