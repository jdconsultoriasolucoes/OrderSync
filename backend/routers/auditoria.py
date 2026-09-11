from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from database import get_db
from models.auditoria import LogisticaAuditoriaModel
from core.deps import get_current_user
from models.usuario import UsuarioModel

router = APIRouter(
    prefix="/api/auditoria",
    tags=["Auditoria"],
    responses={404: {"description": "Not found"}},
)

@router.get("/logistica")
def get_auditoria_logistica(
    skip: int = 0, 
    limit: int = 50, 
    tipo: str = None, 
    db: Session = Depends(get_db), 
    current_user: UsuarioModel = Depends(get_current_user)
):
    query = db.query(LogisticaAuditoriaModel)
    
    if tipo:
        query = query.filter(LogisticaAuditoriaModel.tipo_operacao == tipo.upper())
        
    auditoria = query.order_by(desc(LogisticaAuditoriaModel.data_finalizacao)).offset(skip).limit(limit).all()
    
    # Optional: could parse snapshot_dados here if frontend prefers object over string
    # For now, returning as is because the frontend might want to parse it explicitly
    return auditoria

@router.get("/logistica/{id}")
def get_auditoria_logistica_detail(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: UsuarioModel = Depends(get_current_user)
):
    auditoria = db.query(LogisticaAuditoriaModel).filter(LogisticaAuditoriaModel.id == id).first()
    if not auditoria:
        raise HTTPException(status_code=404, detail="Registro de auditoria não encontrado")
    
    return auditoria
