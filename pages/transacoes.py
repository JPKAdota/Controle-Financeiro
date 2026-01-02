import streamlit as st
import pandas as pd
from datetime import datetime
from modules.ui import setup_styles, exibir_card_metrica, formatar_moeda
from modules.processador import ProcessadorExtratos

st.set_page_config(
    page_title="Transações - Controle Financeiro",
    page_icon="💳",
    layout="wide"
)

setup_styles()
st.title("💳 Gerenciar Transações")

# Inicializa dados se vazio
if 'df_transacoes' not in st.session_state:
    st.session_state.df_transacoes = pd.DataFrame(columns=['data', 'descricao', 'valor', 'categoria', 'tipo', 'fonte'])

df = st.session_state.df_transacoes

# --- 1. Botão de Adicionar (Inserir) ---
with st.expander("➕ Adicionar Nova Transação", expanded=False):
    with st.form("nova_transacao"):
        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data", value=datetime.today())
            descricao_input = st.text_input("Descrição", placeholder="Ex: Mercado Livre")
            categoria_input = st.selectbox("Categoria", [
                "Comida", "Transporte", "Moradia", "Lazer", "Saúde", "Educação", "Investimentos", "Salário", "Outros"
            ])
        
        with col2:
            valor_input = st.number_input("Valor (R$)", min_value=0.01, step=1.00)
            tipo_input = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
            fonte_input = "Manual"
        
        submitted = st.form_submit_button("Salvar Transação")
        
        if submitted:
            # Lógica para salvar
            valor_final = valor_input if tipo_input == "Receita" else -abs(valor_input)
            
            nova_linha = {
                'data': data_input.strftime('%d/%m/%Y'),
                'descricao': descricao_input,
                'valor': valor_final,
                'categoria': categoria_input,
                'tipo': tipo_input,
                'fonte': fonte_input
            }
            
            # Adiciona ao dataframe
            st.session_state.df_transacoes = pd.concat(
                [st.session_state.df_transacoes, pd.DataFrame([nova_linha])], 
                ignore_index=True
            )
            st.success("✅ Transação adicionada com sucesso!")
            st.rerun()

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# --- 2. Métricas Rápidas ---
if not df.empty:
    processador = ProcessadorExtratos()
    metricas = processador.calcular_metricas(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        exibir_card_metrica("Total Receitas", formatar_moeda(metricas['receitas_total']), "receita")
    with col2:
        exibir_card_metrica("Total Despesas", formatar_moeda(metricas['despesas_total']), "despesa")
    with col3:
        exibir_card_metrica("Saldo Atual", formatar_moeda(metricas['saldo']), "saldo")
else:
    st.info("Nenhuma transação registrada.")

# --- 3. Tabela Editável (Editar / Excluir) ---
st.markdown("### 📝 Edição e Exclusão")
st.markdown("Use a tabela abaixo para **editar** valores diretamente ou **excluir** linhas selecionando-as e clicando em 'delete'.")

if not df.empty:
    # Configuração da coluna de dados para editor
    column_config = {
        "valor": st.column_config.NumberColumn(
            "Valor (R$)",
            format="R$ %.2f"
        ),
        "categoria": st.column_config.SelectboxColumn(
            "Categoria",
            options=["Comida", "Transporte", "Moradia", "Lazer", "Saúde", "Educação", "Investimentos", "Salário", "Outros"],
            required=True
        ),
        "tipo": st.column_config.SelectboxColumn(
            "Tipo",
            options=["Receita", "Despesa"],
            required=True
        ),
        "data": st.column_config.TextColumn(
            "Data",
            help="Formato DD/MM/AAAA"
        )
    }

    # Data Editor
    df_editado = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic", # Permite adicionar/remover linhas
        width="stretch",
        hide_index=True,
        key="editor_transacoes"
    )

    # Botão para salvar alterações em massa (opcional, o data_editor já atualiza o state se configurado, 
    # mas como estamos usando st.session_state.df_transacoes como input, precisamos atualizar o state explicitamente com o output)
    
    # Atualização Automática:
    # O Streamlit reinicia o script quando o data_editor muda.
    # Precisamos comparar se houve mudança para atualizar o session_state
    
    if not df.equals(df_editado):
        st.session_state.df_transacoes = df_editado
        st.success("💾 Alterações salvas automaticamente!")
        # Não damos rerun aqui para evitar loop infinito visual, mas o dado já está salvo
else:
    st.warning("Ainda não há dados para editar. Adicione acima.")
