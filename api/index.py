from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from api.processor import ProcessadorExtratos
from fastapi.middleware.cors import CORSMiddleware
import io

app = FastAPI()

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

from api.database import DatabaseManager

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
