import streamlit as st

def setup_styles():
    """Define CSS global para a aplicação."""
    st.markdown("""
    <style>
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .card-receita { border-left: 5px solid #00cc00; }
        .card-despesa { border-left: 5px solid #ff4b4b; }
        .card-saldo { border-left: 5px solid #1f77b4; }
        .card-investimentos { border-left: 5px solid #ffaa00; }
        .card-poupanca { border-left: 5px solid #6a0dad; }
        
        .metric-title {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }
        .metric-subtitle {
            font-size: 0.8rem;
        }
        .positive { color: #00cc00; }
        .negative { color: #ff4b4b; }
        .neutral { color: #666; }
    </style>
    """, unsafe_allow_html=True)

def exibir_card_metrica(titulo, valor, tipo="neutro", subtitulo=None):
    """
    Exibe um card de métrica.
    tipo: 'receita', 'despesa', 'saldo', 'investimentos', 'poupanca', 'neutro'
    """
    cores = {
        'receita': '#00cc00',
        'despesa': '#ff4b4b',
        'saldo': '#1f77b4',
        'investimentos': '#ffaa00',
        'poupanca': '#6a0dad',
        'neutro': '#666'
    }
    
    cor = cores.get(tipo, '#666')
    classe_borda = f"card-{tipo}" if tipo in cores else ""
    
    html_subtit = ""
    if subtitulo:
        html_subtit = f'<div class="metric-subtitle neutral">{subtitulo}</div>'
    
    st.markdown(f"""
    <div class="metric-card {classe_borda}">
        <div class="metric-title">{titulo}</div>
        <div class="metric-value" style="color: {cor};">{valor}</div>
        {html_subtit}
    </div>
    """, unsafe_allow_html=True)

def formatar_moeda(valor):
    """Formata float para string de moeda BRL"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
