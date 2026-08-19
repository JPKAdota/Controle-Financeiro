from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Query, Request
import sys
import os

# Adiciona o diretório atual ao path para que imports relativos funcionem na Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from processor import ProcessadorExtratos
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import io

app = FastAPI()

# --- Imports dos novos serviços ---
from market_service import (
    get_stock_quotes, get_macro_indicators, get_stock_history,
    get_stock_dividends, get_fii_dividends, get_crypto_quotes, search_tickers
)
from chat_service import chat_with_agent, get_suggested_questions
from simulator_service import simulate_investment, compare_scenarios
from database import DatabaseError, DatabaseManager

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
auth_scheme = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS", "http://localhost:3000"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def api_root():
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=frontend_url)


@app.exception_handler(DatabaseError)
async def database_error_handler(_: Request, exc: DatabaseError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticação obrigatória.")

    try:
        auth_client = DatabaseManager()._require_client()
        user_response = auth_client.auth.get_user(credentials.credentials)
        user = user_response.user
        if not user:
            raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
        return {"id": user.id, "access_token": credentials.credentials}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.") from exc


def get_user_database(user=Depends(get_current_user)):
    return DatabaseManager(user["access_token"])

class Transacao(BaseModel):
    data: str = Field(min_length=8, max_length=30)
    descricao: str = Field(min_length=1, max_length=300)
    valor: float = Field(allow_inf_nan=False)
    categoria: str = Field(min_length=1, max_length=100)
    tipo: Literal["Receita", "Despesa", "Investimento"]
    fonte: str = Field(min_length=1, max_length=50)
    data_vencimento: Optional[str] = Field(default=None, max_length=30)

class ProcessResult(BaseModel):
    message: str
    transacoes: List[Transacao]
    metricas: Optional[dict] = None

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/transactions")
def get_transactions(db=Depends(get_user_database)):
    return db.get_transactions()

@app.get("/api/categories")
def get_categories(db=Depends(get_user_database)):
    return db.get_categories()

class CategoryModel(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    tipo: Literal["Despesa", "Receita", "Investimento"]

@app.post("/api/categories")
def add_category(cat: CategoryModel, db=Depends(get_user_database)):
    try:
        db.add_category(cat.nome, cat.tipo)
        return {"message": "Categoria adicionada"}
    except DatabaseError:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/categories/{id}")
def delete_category(id: str, db=Depends(get_user_database)):
    db.delete_category(id)
    return {"message": "Categoria removida"}

@app.put("/api/categories/{id}")
def update_category(id: str, cat: CategoryModel, db=Depends(get_user_database)):
    db.update_category(id, cat.nome, cat.tipo)
    return {"message": "Categoria atualizada"}

@app.post("/api/transactions")
def add_transaction(t: Transacao, db=Depends(get_user_database)):
    try:
        # Convert Pydantic model to dict
        db.add_manual_transaction(t.dict())
        return {"message": "Transação adicionada"}
    except DatabaseError:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/transactions/{id}")
def delete_transaction(id: str, db=Depends(get_user_database)):
    db.delete_transaction(id)
    return {"message": "Transação removida"}

@app.delete("/api/transactions-all")
def delete_all_transactions(db=Depends(get_user_database)):
    db.delete_all_transactions()
    return {"message": "Todas as transações foram removidas"}

class UpdateTransactionModel(BaseModel):
    categoria: Optional[str] = Field(default=None, min_length=1, max_length=100)
    descricao: Optional[str] = Field(default=None, min_length=1, max_length=300)
    valor: Optional[float] = Field(default=None, allow_inf_nan=False)
    data: Optional[str] = Field(default=None, min_length=8, max_length=30)
    tipo: Optional[Literal["Receita", "Despesa", "Investimento"]] = None
    data_vencimento: Optional[str] = Field(default=None, max_length=30)

@app.put("/api/transactions/{id}")
def update_transaction(id: str, t: UpdateTransactionModel, db=Depends(get_user_database)):
    # Filter only provided fields
    data_to_update = {k: v for k, v in t.dict().items() if v is not None}
    if data_to_update:
        db.update_transaction(id, data_to_update)
    return {"message": "Transação atualizada"}

@app.get("/api/dashboard-charts")
def get_dashboard_charts(db=Depends(get_user_database)):
    return db.get_dashboard_data()

@app.post("/api/process-upload", response_model=ProcessResult)
async def process_upload(file: UploadFile = File(...), db=Depends(get_user_database)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome")

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in {".pdf", ".csv"}:
        raise HTTPException(status_code=400, detail="Formato não suportado. Use PDF ou CSV.")

    contents = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 10 MB.")

    processador = ProcessadorExtratos()
    
    try:
        transacoes = []
        if extension == ".pdf":
            transacoes = processador.processar_pdf(contents)
        elif extension == ".csv":
            transacoes = processador.processar_csv(contents)
            
        # Salva no banco se estiver configurado
        db.save_transactions(transacoes)
            
        return {
            "message": f"Processado com sucesso. {len(transacoes)} transações encontradas e salvas.",
            "transacoes": transacoes
        }
    except (DatabaseError, HTTPException):
        raise
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
    message: str = Field(min_length=1, max_length=4000)
    context: Optional[dict] = None
    history: Optional[List[dict]] = Field(default=None, max_length=20)


@app.post("/api/agent/chat")
async def agent_chat(req: ChatRequest, db=Depends(get_user_database)):
    """Chat com o assistente de investimentos IA."""
    # Se contexto não foi enviado, buscar dados do usuário automaticamente
    context = req.context
    if not context:
        try:
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

    result = await chat_with_agent(
        message=req.message,
        context=context,
        history=req.history,
    )

    if result.get("error"):
        status_by_error = {
            "ollama_unavailable": 503,
            "api_key_missing": 503,
            "module_not_installed": 503,
            "ollama_timeout": 504,
            "rate_limited": 429,
        }
        raise HTTPException(
            status_code=status_by_error.get(result["error"], 502),
            detail=result.get("response", "Provedor de IA indisponível."),
        )

    return result


@app.get("/api/agent/suggestions")
def agent_suggestions():
    """Retorna sugestões de perguntas para o chat."""
    return {"suggestions": get_suggested_questions()}


# --- SIMULADOR ---

class SimulateRequest(BaseModel):
    aporte_inicial: float = Field(default=0, ge=0, allow_inf_nan=False)
    aporte_mensal: float = Field(default=0, ge=0, allow_inf_nan=False)
    taxa_anual: float = Field(default=12.0, ge=-100, allow_inf_nan=False)
    meses: int = Field(default=12, ge=1, le=600)
    indexador: Literal["pre", "cdi", "ipca"] = "pre"
    taxa_indexador: float = Field(default=0.0, ge=-100, allow_inf_nan=False)


@app.post("/api/agent/simulate")
def agent_simulate(req: SimulateRequest):
    """Simula a evolução de um investimento."""
    return simulate_investment(
        aporte_inicial=req.aporte_inicial,
        aporte_mensal=req.aporte_mensal,
        taxa_anual=req.taxa_anual,
        meses=req.meses,
        indexador=req.indexador,
        taxa_indexador=req.taxa_indexador,
    )


class CompareRequest(BaseModel):
    scenarios: List[dict] = Field(min_length=1, max_length=3)


@app.post("/api/agent/compare")
def agent_compare(req: CompareRequest):
    """Compara múltiplos cenários de investimento."""
    if len(req.scenarios) < 1 or len(req.scenarios) > 3:
        raise HTTPException(status_code=400, detail="Envie entre 1 e 3 cenários")
    return compare_scenarios(req.scenarios)

