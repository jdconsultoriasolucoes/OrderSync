from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from typing import List, Dict, Any

router = APIRouter(prefix="/api/fornecedores", tags=["Fornecedores"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=List[Dict[str, Any]])
def listar_fornecedores(db: Session = Depends(get_db)):
    """
    Lista todos os fornecedores da tabela t_fornecedor.
    Retorna apenas id e nome_fornecedor.
    """
    # Usando raw SQL para garantir compatibilidade inicial, ou poderia usar o Model.
    # Como o user pediu "trazer a informação de nome_fornecedor", vamos focar nisso.
    
    try:
        results = db.execute(text("SELECT id, nome_fornecedor FROM t_fornecedor ORDER BY nome_fornecedor ASC")).mappings().all()
        return [dict(row) for row in results]
    except Exception as e:
        # Se a tabela não existir ou tiver erro, retorna vazio ou erro tratado
        print(f"Erro ao listar fornecedores: {e}")
        return []
