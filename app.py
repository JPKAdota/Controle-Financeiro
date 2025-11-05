import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Controle Financeiro IA",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para cards estilo imagem COM CORES
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .card-receita {
        border-left: 5px solid #00cc00;
    }
    .card-gastos {
        border-left: 5px solid #ff4b4b;
    }
    .card-saldo {
        border-left: 5px solid #1f77b4;
    }
    .card-investimentos {
        border-left: 5px solid #ffaa00;
    }
    .card-poupanca {
        border-left: 5px solid #6a0dad;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.25rem;
    }
    .metric-subtitle {
        font-size: 0.8rem;
    }
    .positive {
        color: #00cc00;
    }
    .negative {
        color: #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<div class="main-header">💰 Controle Financeiro IA</div>', unsafe_allow_html=True)

# Cards principais estilo imagem COM CORES
st.markdown("## Setembro 2025")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    <div class="metric-card card-receita">
        <div class="metric-title">Receitas (set)</div>
        <div class="metric-value" style="color: #00cc00;">R$ 15.500,29</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card card-gastos">
        <div class="metric-title">Gastos (set)</div>
        <div class="metric-value" style="color: #ff4b4b;">R$ 7.519,97</div>
        <div class="metric-subtitle negative">37.0% vs mês anterior</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card card-saldo">
        <div class="metric-title">Saldo (set)</div>
        <div class="metric-value" style="color: #1f77b4;">R$ 7.980,32</div>
        <div class="metric-subtitle positive">Superávit mensal</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card card-investimentos">
        <div class="metric-title">Investimentos</div>
        <div class="metric-value" style="color: #ffaa00;">R$ 0,00</div>
        <div class="metric-subtitle positive">+0,1% retorno</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="metric-card card-poupanca">
        <div class="metric-title">Taxa de Poupança</div>
        <div class="metric-value" style="color: #6a0dad;">51.5%</div>
    </div>
    """, unsafe_allow_html=True)

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# Mensagem de boas-vindas
st.markdown("""
## Bem-vindo ao seu Controle Financeiro Inteligente! 🚀

**👉 Use o menu lateral para navegar entre as páginas.**
""")