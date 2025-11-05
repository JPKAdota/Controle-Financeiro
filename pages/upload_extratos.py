import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o diretório modules ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.processador import ProcessadorExtratos

st.title("📤 Upload do Extrato Bancário")

st.markdown("""
Envie seu extrato bancário (PDF ou CSV) e deixe a IA analisar seus gastos automaticamente.

**Formatos suportados:**
- 📄 **PDF**: Extratos bancários completos
- 📊 **CSV**: Planilhas exportadas do internet banking

A IA irá extrair, categorizar e analisar automaticamente!
""")

# Inicializa o processador
processador = ProcessadorExtratos()

# Área de upload
st.subheader("📎 Enviar Extrato")

uploaded_file = st.file_uploader(
    "Arraste e solte seu arquivo aqui ou clique para selecionar",
    type=['csv', 'pdf'],  # ← AGORA ACEITA PDF TAMBÉM
    accept_multiple_files=False,
    key="file_uploader"
)

if uploaded_file is not None:
    st.success(f"✅ Arquivo '{uploaded_file.name}' carregado com sucesso!")
    st.write(f"📋 **Tipo:** {uploaded_file.type} | **Tamanho:** {uploaded_file.size / 1024:.1f} KB")
    
    # Mostrar preview baseado no tipo
    if uploaded_file.type == "text/csv":
        st.subheader("👀 Pré-visualização do CSV")
        try:
            df_preview = pd.read_csv(uploaded_file)
            st.write(f"**Formato:** {df_preview.shape[0]} linhas × {df_preview.shape[1]} colunas")
            st.dataframe(df_preview.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erro ao ler CSV: {e}")
    
    elif uploaded_file.type == "application/pdf":
        st.subheader("📄 Informações do PDF")
        st.info("""
        **Processamento de PDF:**
        - ✅ Extração automática de texto
        - ✅ Identificação de transações
        - ✅ Categorização inteligente
        - ⚠️ A precisão depende do formato do seu banco
        """)
    
    # Botão para processar
    if st.button("🔍 Processar com IA", type="primary"):
        with st.spinner("🤖 Processando extrato com IA..."):
            # Processa o arquivo (CSV ou PDF)
            df_processado = processador.processar_arquivo(uploaded_file)
            
            if df_processado is not None and not df_processado.empty:
                st.success(f"✅ Análise concluída! {len(df_processado)} transações processadas.")
                
                # Calcula métricas
                metricas = processador.calcular_metricas(df_processado)
                
                # Mostra resultados
                st.subheader("📈 Resultados da Análise")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Receitas", f"R$ {metricas['receitas_total']:,.2f}")
                
                with col2:
                    st.metric("Total Despesas", f"R$ {metricas['despesas_total']:,.2f}")
                
                with col3:
                    st.metric("Saldo", f"R$ {metricas['saldo']:,.2f}")
                
                with col4:
                    st.metric("Taxa Poupança", f"{metricas['taxa_poupanca']:.1f}%")
                
                # Transações processadas
                st.subheader(f"💳 {len(df_processado)} Transações Categorizadas")
                st.dataframe(df_processado, use_container_width=True)
                
                # Gráfico de categorias
                st.subheader("📊 Distribuição por Categoria")
                
                if not df_processado.empty:
                    gastos_por_categoria = df_processado[df_processado['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().abs()
                    
                    if not gastos_por_categoria.empty:
                        df_categorias = pd.DataFrame({
                            'Categoria': gastos_por_categoria.index,
                            'Valor': gastos_por_categoria.values
                        })
                        
                        import plotly.express as px
                        fig = px.pie(df_categorias, values='Valor', names='Categoria', 
                                    title='Gastos por Categoria')
                        st.plotly_chart(fig, use_container_width=True)
                
                # Salva na sessão para usar em outras páginas
                st.session_state.df_transacoes = df_processado
                st.session_state.metricas = metricas
                
                st.balloons()
                
            else:
                st.error("❌ Não foi possível processar o arquivo. Verifique o formato.")
else:
    st.info("👆 **Selecione um arquivo PDF ou CSV para começar a análise**")

# Exemplos de formatos
with st.expander("📋 Exemplos de Formatos Suportados"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Formato CSV:**")
        st.code("""
Data,Descrição,Valor
2025-09-01,Supermercado Extra,-350.50
2025-09-02,Posto Ipiranga,-80.00
2025-09-05,Salário Empresa XYZ,5000.00
        """, language="text")
    
    with col2:
        st.markdown("**📄 Formato PDF:**")
        st.markdown("""
        Extratos bancários padrão contendo:
        - Datas das transações
        - Descrições dos lançamentos  
        - Valores (débitos/créditos)
        - **Exemplo de bancos:**
          - Itaú, Bradesco, Santander
          - Nubank, Inter, C6 Bank
          - BB, Caixa, etc.
        """)

