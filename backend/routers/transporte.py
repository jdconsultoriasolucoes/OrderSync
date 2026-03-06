from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.transporte import TransporteModel
from schemas.transporte import TransporteCreate, TransporteUpdate, TransporteResponse
from datetime import datetime

router = APIRouter(
    prefix="/api/transporte",
    tags=["Transporte"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=TransporteResponse, status_code=status.HTTP_201_CREATED)
def create_transporte(transporte: TransporteCreate, db: Session = Depends(get_db)):
    db_transporte = TransporteModel(**transporte.model_dump())
    db.add(db_transporte)
    db.commit()
    db.refresh(db_transporte)
    return db_transporte

@router.get("", response_model=List[TransporteResponse])
def read_transportes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transportes = db.query(TransporteModel).filter(TransporteModel.data_desativacao == None).offset(skip).limit(limit).all()
    return transportes

@router.get("/{transporte_id}", response_model=TransporteResponse)
def read_transporte(transporte_id: int, db: Session = Depends(get_db)):
    db_transporte = db.query(TransporteModel).filter(TransporteModel.id == transporte_id).first()
    if db_transporte is None:
        raise HTTPException(status_code=404, detail="Transporte não encontrado")
    return db_transporte

@router.put("/{transporte_id}", response_model=TransporteResponse)
def update_transporte(transporte_id: int, transporte: TransporteUpdate, db: Session = Depends(get_db)):
    db_transporte = db.query(TransporteModel).filter(TransporteModel.id == transporte_id).first()
    if db_transporte is None:
        raise HTTPException(status_code=404, detail="Transporte não encontrado")
    
    update_data = transporte.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transporte, key, value)
        
    db.commit()
    db.refresh(db_transporte)
    return db_transporte

@router.delete("/{transporte_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transporte(transporte_id: int, db: Session = Depends(get_db)):
    db_transporte = db.query(TransporteModel).filter(TransporteModel.id == transporte_id).first()
    if db_transporte is None:
        raise HTTPException(status_code=404, detail="Transporte não encontrado")
    
    db_transporte.data_desativacao = datetime.utcnow()
    db.commit()
    return None
