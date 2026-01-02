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
