import streamlit as st
import pandas as pd

st.title("💳 Todas as Transações")

# CSS para melhorar layout
st.markdown("""
<style>
    .transaction-card {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Filtros com mais espaço
st.markdown("### Filtros")
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    busca = st.text_input("🔍 Buscar por descrição...")

with col2:
    categoria = st.selectbox("📂 Categoria", ["Todas", "Comida", "Transporte", "Moradia", "Lazer", "Saúde", "Educação"])

with col3:
    tipo = st.selectbox("💰 Tipo", ["Todos", "Receita", "Despesa"])

with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Filtrar"):
        st.success("Filtros aplicados!")

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# Métricas
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: #f0f8ff; padding: 1rem; border-radius: 10px; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">Total Receitas</div>
        <div style="font-size: 1.5rem; font-weight: bold; color: #00cc00;">R$ 96.907,58</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: #fff0f0; padding: 1rem; border-radius: 10px; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">Total Despesas</div>
        <div style="font-size: 1.5rem; font-weight: bold; color: #ff4b4b;">R$ 71.501,84</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: #f0fff0; padding: 1rem; border-radius: 10px; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">Saldo Atual</div>
        <div style="font-size: 1.5rem; font-weight: bold; color: #1f77b4;">R$ 25.405,74</div>
    </div>
    """, unsafe_allow_html=True)

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# Tabela de transações
st.markdown("### 📋 172 transações encontradas")

# Dados de exemplo melhor formatados
dados_transacoes = pd.DataFrame({
    'Data': ['07/09/2025', '07/09/2025', '05/09/2025', '03/09/2025', '01/09/2025'],
    'Descrição': ['Conta de energia elétrica - Eletropaulo', 'Rendimento aplicação automática', 'Supermercado - Extra', 'Restaurante - Outback', 'Salário - Empresa XYZ'],
    'Categoria': ['Moradia', 'Investimento', 'Comida', 'Alimentação', 'Receita'],
    'Valor': ['-R$ 98,75', '+R$ 150,42', '-R$ 350,00', '-R$ 120,00', '+R$ 5.000,00']
})

st.dataframe(dados_transacoes, width='stretch', height=300)

# Botão para adicionar transação
st.markdown("<br>", unsafe_allow_html=True)
if st.button("➕ Adicionar Transação Manual", type="primary"):
    st.info("Funcionalidade em desenvolvimento!")