from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
# Se houver modelos ou schemas, importar aqui.

router = APIRouter(prefix="/fornecedor", tags=["Fornecedor"])

@router.get("/")
def listar_fornecedores(db: Session = Depends(get_db)):
    # Retorna lista vazia por enquanto para não quebrar contrato
    return []
