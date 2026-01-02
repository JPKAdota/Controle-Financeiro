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
            st.dataframe(df_preview.head(10), width="stretch")
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
                # Separa o que precisa de revisão
                df_precisa_revisao = df_processado[df_processado['categoria'] == 'A Categorizar']
                df_ok = df_processado[df_processado['categoria'] != 'A Categorizar']
                
                # Estado temporário para revisão
                st.session_state['df_revisao'] = df_precisa_revisao
                st.session_state['df_ok'] = df_ok
                st.session_state['revisao_ativa'] = True
                
            else:
                st.error("❌ Não foi possível processar o arquivo. Verifique o formato.")

    # --- Área de Revisão de Categorias ---
    if st.session_state.get('revisao_ativa'):
        st.markdown("---")
        st.subheader("🕵️‍♀️ Revisão Necessária")
        
        df_revisao = st.session_state['df_revisao']
        df_ok = st.session_state['df_ok']
        
        qtde_pendente = len(df_revisao)
        qtde_ok = len(df_ok)
        
        if qtde_pendente > 0:
            st.warning(f"⚠️ Encontramos **{qtde_pendente}** transações que não conseguimos identificar automaticamente.")
            st.markdown("Por favor, categorize-as abaixo antes de continuar:")
            
            # Editor para categorização manual
            column_config = {
                "categoria": st.column_config.SelectboxColumn(
                    "Categoria",
                    options=["Comida", "Transporte", "Moradia", "Lazer", "Saúde", "Educação", "Investimentos", "Salário", "Outros"],
                    required=True
                )
            }
            
            df_revisado = st.data_editor(
                df_revisao,
                column_config=column_config,
                width="stretch",
                key="editor_revisao",
                disabled=["data", "descricao", "valor", "tipo"] # Bloqueia outros campos
            )
        else:
            st.success("✅ Todas as transações foram identificadas automaticamente!")
            df_revisado = df_revisao # Vazio

        # Botão Final de Confirmação
        if st.button("💾 Confirmar e Salvar Tudo", type="primary"):
            # Junta tudo
            df_final = pd.concat([df_ok, df_revisado], ignore_index=True)
            
            # Salva na sessão
            if 'df_transacoes' not in st.session_state:
                st.session_state.df_transacoes = pd.DataFrame()
            
            st.session_state.df_transacoes = pd.concat([st.session_state.df_transacoes, df_final], ignore_index=True)
            
            # Recalcula métricas globais
            metricas = processador.calcular_metricas(st.session_state.df_transacoes)
            st.session_state.metricas = metricas
            
            st.success(f"🎉 Sucesso! {len(df_final)} transações adicionadas ao seu controle.")
            
            # Limpa estado de revisão
            del st.session_state['revisao_ativa']
            del st.session_state['df_revisao']
            del st.session_state['df_ok']
            st.rerun()
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

