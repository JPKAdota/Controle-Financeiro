import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.title("📊 Dashboard Financeiro")

# CSS para cards com cores
st.markdown("""
<style>
    .dashboard-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .card-receita {
        border-left: 5px solid #00cc00;
    }
    .card-despesa {
        border-left: 5px solid #ff4b4b;
    }
    .card-saldo {
        border-left: 5px solid #1f77b4;
    }
    .card-economia {
        border-left: 5px solid #ffaa00;
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
    .neutral {
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# FILTROS CORRIGIDOS - Simples como na imagem
st.markdown("### Filtros")

col1, col2 = st.columns(2)

with col1:
    # Período com opção "Atual"
    periodo = st.selectbox(
        "Período:", 
        ["Atual", "Últimos 3 meses", "Últimos 6 meses", "Este ano", "Ano anterior"]
    )

with col2:
    # Seletor simples de mês/ano (sem calendário)
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    anos = [2025, 2024, 2023, 2022]
    
    col_ano, col_mes = st.columns(2)
    
    with col_ano:
        ano_selecionado = st.selectbox("Ano:", anos, index=anos.index(ano_atual))
    
    with col_mes:
        mes_selecionado = st.selectbox("Mês:", meses, index=mes_atual-1)

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# Métricas principais em cards COM CORES
st.markdown(f"### Visão Geral - {mes_selecionado} {ano_selecionado}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="dashboard-card card-receita">
        <div class="metric-title">Receitas</div>
        <div class="metric-value" style="color: #00cc00;">R$ 15.500,29</div>
        <div class="metric-subtitle positive">+2% vs anterior</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="dashboard-card card-despesa">
        <div class="metric-title">Despesas</div>
        <div class="metric-value" style="color: #ff4b4b;">R$ 7.519,97</div>
        <div class="metric-subtitle negative">-5% vs anterior</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="dashboard-card card-saldo">
        <div class="metric-title">Saldo</div>
        <div class="metric-value" style="color: #1f77b4;">R$ 7.980,32</div>
        <div class="metric-subtitle positive">+15%</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="dashboard-card card-economia">
        <div class="metric-title">Economia</div>
        <div class="metric-value" style="color: #ffaa00;">51.5%</div>
        <div class="metric-subtitle neutral">Meta: 30%</div>
    </div>
    """, unsafe_allow_html=True)

# Espaçamento entre seções
st.markdown("<br>", unsafe_allow_html=True)

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Evolução Mensal")
    
    dados = pd.DataFrame({
        'Mês': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set'],
        'Receitas': [14200, 14800, 15200, 14900, 15100, 15000, 15300, 15400, 15500],
        'Despesas': [8200, 8100, 8300, 7900, 8000, 7800, 7600, 7500, 7520]
    })
    
    fig = px.line(dados, x='Mês', y=['Receitas', 'Despesas'],
                  title='Receitas vs Despesas - 2025')
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Gastos por Categoria")
    
    categorias = pd.DataFrame({
        'Categoria': ['Comida', 'Transporte', 'Moradia', 'Lazer', 'Saúde', 'Educação'],
        'Valor': [2200, 1500, 1800, 800, 600, 620]
    })
    
    fig = px.pie(categorias, values='Valor', names='Categoria',
                 title='Distribuição de Gastos - Setembro')
    
    st.plotly_chart(fig, use_container_width=True)

# Recomendações da IA
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 💡 Recomendações da IA")

st.markdown("""
<div style="background: white; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #6a0dad; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <strong style="color: #6a0dad;">📈 Análise do seu padrão de gastos:</strong><br><br>
    
    🍽️ <strong>Comida:</strong> Você gastou R$ 2.200 este mês (29% das despesas)<br>
    <em style="color: #666;">Sugestão: Reduzir delivery em 20% pode economizar R$ 440/mês</em><br><br>
    
    🚗 <strong>Transporte:</strong> R$ 1.500 (20% das despesas)<br>
    <em style="color: #666;">Sugestão: Carona solidária 2x na semana = R$ 300/mês de economia</em><br><br>
    
    💡 <strong>Próxima meta:</strong> Aumentar taxa de poupança para 55% (+R$ 200/mês)
</div>
""", unsafe_allow_html=True)