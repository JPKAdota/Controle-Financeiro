import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modules.ui import setup_styles, exibir_card_metrica, formatar_moeda
from modules.processador import ProcessadorExtratos

st.set_page_config(
    page_title="Dashboard - Controle Financeiro",
    page_icon="📊", 
    layout="wide"
)

# Inicializa estilos
setup_styles()

st.title("📊 Dashboard Financeiro")

# Verifica se existe dados
if 'df_transacoes' not in st.session_state or st.session_state.df_transacoes.empty:
    st.warning("⚠️ Nenhum dado encontrado. Faça upload de um extrato ou adicione transações manualmente.")
    st.info("💡 Vá até 'Upload Extratos' no menu lateral para começar.")
    st.stop()

# Recupera dados
df = st.session_state.df_transacoes
processador = ProcessadorExtratos()
metricas = processador.calcular_metricas(df)

# Filtros (Simplificado para MVP)
# st.markdown("### Filtros")
# col1, col2 = st.columns(2)
# ... implementar filtros reais depois ...

# Métricas principais
st.markdown("### Visão Geral")

col1, col2, col3, col4 = st.columns(4)

with col1:
    exibir_card_metrica("Receitas", formatar_moeda(metricas['receitas_total']), "receita")

with col2:
    exibir_card_metrica("Despesas", formatar_moeda(metricas['despesas_total']), "despesa")

with col3:
    st.markdown("""
    <div class="dashboard-card card-saldo">
        <div class="metric-title">Saldo</div>
        <div class="metric-value" style="color: #1f77b4;">{saldo}</div>
        <div class="metric-subtitle positive">Conta Corrente</div>
    </div>
    """.format(saldo=formatar_moeda(metricas['saldo'])), unsafe_allow_html=True)

with col4:
    # Mostra Investimentos
    valor_investido = metricas.get('investimentos_total', 0)
    st.markdown("""
    <div class="dashboard-card card-economia">
        <div class="metric-title">Investido (Mês)</div>
        <div class="metric-value" style="color: #ffaa00;">{invest}</div>
        <div class="metric-subtitle neutral">Taxa: {taxa:.1f}%</div>
    </div>
    """.format(invest=formatar_moeda(valor_investido), taxa=metricas['taxa_poupanca']), unsafe_allow_html=True)

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Evolução por Fonte")
    # Agrupando por data e tipo
    
    # Tratamento simples de data (assumindo formato DD/MM/AAAA)
    try:
        df['data_dt'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df_chart = df.sort_values('data_dt')
    except:
        df_chart = df # Fallback

    fig_evolucao = px.bar(
        df_chart, 
        x='data', 
        y='valor', 
        color='tipo', 
        title='Fluxo de Caixa',
        color_discrete_map={'Receita': '#00cc00', 'Despesa': '#ff4b4b'}
    )
    st.plotly_chart(fig_evolucao, width="stretch")

with col2:
    st.markdown("#### Gastos por Categoria")
    
    df_despesas = df[df['tipo'] == 'Despesa']
    if not df_despesas.empty:
        gastos_cat = df_despesas.groupby('categoria')['valor'].sum().abs().reset_index()
        fig_pizza = px.pie(
            gastos_cat, 
            values='valor', 
            names='categoria', 
            title='Distribuição de Gastos',
            donut=True
        )
        st.plotly_chart(fig_pizza, width="stretch")
    else:
        st.info("Nenhuma despesa para exibir no gráfico.")

# Recomendações da IA (Simulada por regras simples por enquanto)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 💡 Insights Automatizados")

if metricas['saldo'] > 0:
    msg_analise = f"🎉 Parabéns! Você está com saldo positivo de {formatar_moeda(metricas['saldo'])}. Que tal investir 50% desse valor?"
    cor_borda = "#00cc00"
else:
    msg_analise = f"⚠️ Atenção! Você está gastando mais do que ganha. Revise suas despesas da categoria 'Lazer' ou 'Comida'."
    cor_borda = "#ff4b4b"

st.markdown(f"""
<div style="background: white; padding: 1.5rem; border-radius: 10px; border-left: 5px solid {cor_borda}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <strong>🤖 Análise Rápida:</strong><br><br>
    {msg_analise}
</div>
""", unsafe_allow_html=True)
