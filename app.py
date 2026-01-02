import streamlit as st
import pandas as pd
from datetime import datetime
from modules.ui import setup_styles, exibir_card_metrica, formatar_moeda
from modules.processador import ProcessadorExtratos

# Configuração da página
st.set_page_config(
    page_title="Controle Financeiro IA",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa estilos globais
setup_styles()

# Inicializa Session State se não existir
if 'df_transacoes' not in st.session_state:
    st.session_state.df_transacoes = pd.DataFrame()
    
    # Dados de exemplo iniciais (para não ficar vazio na primeira visita)
    # Comente estas linhas se quiser começar VAZIO
    dados_exemplo = {
        'data': [datetime.now().strftime('%d/%m/%Y')],
        'descricao': ['Exemplo - Faça Upload do seu Extrato'],
        'valor': [0.0],
        'categoria': ['Geral'],
        'tipo': ['Receita'],
        'fonte': ['Sistema']
    }
    st.session_state.df_transacoes = pd.DataFrame(dados_exemplo)

# Header principal
st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h1>💰 Controle Financeiro IA</h1></div>', unsafe_allow_html=True)

# Cálculo das métricas reais
df = st.session_state.df_transacoes
processador = ProcessadorExtratos()
metricas = processador.calcular_metricas(df) if not df.empty else None

# Título do Mês
mes_ano = datetime.now().strftime("%B %Y").capitalize()
st.markdown(f"## Visão Geral ({mes_ano})")

if metricas:
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        exibir_card_metrica(
            "Receitas", 
            formatar_moeda(metricas['receitas_total']), 
            "receita"
        )

    with col2:
        exibir_card_metrica(
            "Despesas", 
            formatar_moeda(metricas['despesas_total']), 
            "despesa"
        )

    with col3:
        exibir_card_metrica(
            "Saldo", 
            formatar_moeda(metricas['saldo']), 
            "saldo"
        )

    with col4:
        # Mostra o valor de investimentos (Aplicações)
        valor_investido = metricas.get('investimentos_total', 0)
        exibir_card_metrica(
            "Investimentos", 
            formatar_moeda(valor_investido), 
            "investimentos"
        )

    with col5:
        taxa = metricas['taxa_poupanca']
        exibir_card_metrica(
            "Taxa de Poupança", 
            f"{taxa:.1f}%", 
            "poupanca"
        )
else:
    st.info("👋 **Bem-vindo!** Para ver seus números, vá até a página **Upload de Extratos** e envie seus arquivos.")

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# Mensagem de boas-vindas
st.markdown("""
### 🚀 Como começar:
1. Vá até a página **📤 Upload Extratos** no menu lateral.
2. Envie seu extrato em **PDF** ou **CSV**.
3. A IA vai categorizar tudo automaticamente.
4. Volte aqui ou vá em **📊 Dashboard** para ver a mágica!
""")
