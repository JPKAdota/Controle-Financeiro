from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import sys
import os

# Adiciona o diretório atual ao path para que imports relativos funcionem na Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pydantic import BaseModel
from typing import List, Optional
from processor import ProcessadorExtratos
from fastapi.middleware.cors import CORSMiddleware
import io

app = FastAPI()

# --- Imports dos novos serviços ---
from market_service import (
    get_stock_quotes, get_macro_indicators, get_stock_history,
    get_stock_dividends, get_fii_dividends, get_crypto_quotes, search_tickers
)
from chat_service import chat_with_agent, get_suggested_questions
from simulator_service import simulate_investment, compare_scenarios

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Transacao(BaseModel):
    data: str
    descricao: str
    valor: float
    categoria: str
    tipo: str
    fonte: str
    data_vencimento: Optional[str] = None

class ProcessResult(BaseModel):
    message: str
    transacoes: List[Transacao]
    metricas: Optional[dict] = None

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

from database import DatabaseManager

@app.get("/api/transactions")
def get_transactions():
    db = DatabaseManager()
    if not db.client:
        return {"message": "Banco de dados não conectado", "data": []}
    return db.get_transactions()

@app.get("/api/categories")
def get_categories():
    db = DatabaseManager()
    return db.get_categories()

class CategoryModel(BaseModel):
    nome: str
    tipo: str

@app.post("/api/categories")
def add_category(cat: CategoryModel):
    db = DatabaseManager()
    try:
        db.add_category(cat.nome, cat.tipo)
        return {"message": "Categoria adicionada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/categories/{id}")
def delete_category(id: str):
    db = DatabaseManager()
    db.delete_category(id)
    return {"message": "Categoria removida"}

@app.put("/api/categories/{id}")
def update_category(id: str, cat: CategoryModel):
    db = DatabaseManager()
    db.update_category(id, cat.nome, cat.tipo)
    return {"message": "Categoria atualizada"}

@app.post("/api/transactions")
def add_transaction(t: Transacao):
    db = DatabaseManager()
    try:
        # Convert Pydantic model to dict
        db.add_manual_transaction(t.dict())
        return {"message": "Transação adicionada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/transactions/{id}")
def delete_transaction(id: str):
    db = DatabaseManager()
    db.delete_transaction(id)
    return {"message": "Transação removida"}

@app.delete("/api/transactions-all")
def delete_all_transactions():
    db = DatabaseManager()
    db.delete_all_transactions()
    return {"message": "Todas as transações foram removidas"}

class UpdateTransactionModel(BaseModel):
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[str] = None
    tipo: Optional[str] = None
    data_vencimento: Optional[str] = None

@app.put("/api/transactions/{id}")
def update_transaction(id: str, t: UpdateTransactionModel):
    db = DatabaseManager()
    # Filter only provided fields
    data_to_update = {k: v for k, v in t.dict().items() if v is not None}
    if data_to_update:
        db.update_transaction(id, data_to_update)
    return {"message": "Transação atualizada"}

@app.get("/api/dashboard-charts")
def get_dashboard_charts():
    db = DatabaseManager()
    return db.get_dashboard_data()

@app.post("/api/process-upload", response_model=ProcessResult)
async def process_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome")
    
    contents = await file.read()
    processador = ProcessadorExtratos()
    db = DatabaseManager()
    
    try:
        transacoes = []
        if file.filename.endswith('.pdf'):
            transacoes = processador.processar_pdf(contents)
        elif file.filename.endswith('.csv'):
            transacoes = processador.processar_csv(contents)
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado. Use PDF ou CSV.")
            
        # Salva no banco se estiver configurado
        if db.client:
            db.save_transactions(transacoes)
            
        return {
            "message": f"Processado com sucesso. {len(transacoes)} transações encontradas e salvas.",
            "transacoes": transacoes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# AGENTE DE INVESTIMENTOS — NOVOS ENDPOINTS
# =============================================

# --- MERCADO ---

@app.get("/api/market/quotes")
async def market_quotes(symbols: str = Query(default="PETR4,VALE3,ITUB4,MGLU3")):
    """Busca cotações de ações. Symbols separados por vírgula."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return await get_stock_quotes(symbol_list)


@app.get("/api/market/indicators")
async def market_indicators():
    """Retorna indicadores macroeconômicos (Selic, CDI, IPCA, Ibovespa, Dólar)."""
    return await get_macro_indicators()


@app.get("/api/market/history/{symbol}")
async def market_history(symbol: str, range: str = Query(default="1mo", alias="range")):
    """Retorna histórico de preços de um ativo."""
    return await get_stock_history(symbol.upper(), range)


@app.get("/api/market/dividends/{symbol}")
async def market_dividends(symbol: str):
    """Retorna dividendos e JCP de uma ação."""
    return await get_stock_dividends(symbol.upper())


@app.get("/api/market/fii")
async def market_fii(symbols: str = Query(default="MXRF11,HGLG11,XPML11,KNRI11")):
    """Busca rendimentos de FIIs."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return await get_fii_dividends(symbol_list)


@app.get("/api/market/crypto")
async def market_crypto(symbols: str = Query(default="BTC,ETH,SOL")):
    """Busca cotações de criptomoedas."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return await get_crypto_quotes(symbol_list)


@app.get("/api/market/tickers")
async def market_tickers(search: str = Query(default=""), type: str = Query(default="")):
    """Busca e filtra tickers disponíveis na B3."""
    return await search_tickers(search, type)


# --- CHAT IA ---

class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None
    history: Optional[list] = None


@app.post("/api/agent/chat")
async def agent_chat(req: ChatRequest):
    """Chat com o assistente de investimentos IA."""
    # Se contexto não foi enviado, buscar dados do usuário automaticamente
    context = req.context
    if not context:
        try:
            db = DatabaseManager()
            dashboard_data = db.get_dashboard_data()
            transactions = db.get_transactions()
            investments = [
                t for t in transactions
                if t.get("categoria") == "Investimentos" or t.get("tipo") == "Investimento"
            ]
            context = {
                "metrics": dashboard_data.get("metrics", {}),
                "investments": investments[:10],
            }
        except Exception:
            context = {}

    return await chat_with_agent(
        message=req.message,
        context=context,
        history=req.history,
    )


@app.get("/api/agent/suggestions")
def agent_suggestions():
    """Retorna sugestões de perguntas para o chat."""
    return {"suggestions": get_suggested_questions()}


# --- SIMULADOR ---

class SimulateRequest(BaseModel):
    aporte_inicial: float = 0
    aporte_mensal: float = 0
    taxa_anual: float = 12.0
    meses: int = 12
    indexador: str = "pre"
    taxa_indexador: float = 0.0


@app.post("/api/agent/simulate")
def agent_simulate(req: SimulateRequest):
    """Simula a evolução de um investimento."""
    if req.meses < 1 or req.meses > 600:
        raise HTTPException(status_code=400, detail="Período deve ser entre 1 e 600 meses")
    if req.aporte_inicial < 0 or req.aporte_mensal < 0:
        raise HTTPException(status_code=400, detail="Valores de aporte não podem ser negativos")

    return simulate_investment(
        aporte_inicial=req.aporte_inicial,
        aporte_mensal=req.aporte_mensal,
        taxa_anual=req.taxa_anual,
        meses=req.meses,
        indexador=req.indexador,
        taxa_indexador=req.taxa_indexador,
    )


class CompareRequest(BaseModel):
    scenarios: list[dict]


@app.post("/api/agent/compare")
def agent_compare(req: CompareRequest):
    """Compara múltiplos cenários de investimento."""
    if len(req.scenarios) < 1 or len(req.scenarios) > 3:
        raise HTTPException(status_code=400, detail="Envie entre 1 e 3 cenários")
    return compare_scenarios(req.scenarios)

