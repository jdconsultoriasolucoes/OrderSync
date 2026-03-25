from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.vendedor import VendedorModel
from schemas.vendedor import VendedorCreate, VendedorUpdate, VendedorResponse

router = APIRouter()

@router.get("/", response_model=List[VendedorResponse])
def listar_vendedores(db: Session = Depends(get_db)):
    return db.query(VendedorModel).order_by(VendedorModel.nome).all()

@router.post("/", response_model=VendedorResponse, status_code=status.HTTP_201_CREATED)
def criar_vendedor(vendedor: VendedorCreate, db: Session = Depends(get_db)):
    novo_vendedor = VendedorModel(**vendedor.dict())
    db.add(novo_vendedor)
    db.commit()
    db.refresh(novo_vendedor)
    return novo_vendedor

@router.put("/{id}", response_model=VendedorResponse)
def atualizar_vendedor(id: int, vendedor: VendedorUpdate, db: Session = Depends(get_db)):
    db_vendedor = db.query(VendedorModel).filter(VendedorModel.id == id).first()
    if not db_vendedor:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
    
    for key, value in vendedor.dict().items():
        setattr(db_vendedor, key, value)
        
    db.commit()
    db.refresh(db_vendedor)
    return db_vendedor

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_vendedor(id: int, db: Session = Depends(get_db)):
    db_vendedor = db.query(VendedorModel).filter(VendedorModel.id == id).first()
    if not db_vendedor:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
        
    db.delete(db_vendedor)
    db.commit()
    return None
