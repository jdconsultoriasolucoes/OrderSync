from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from database import SessionLocal
from core.deps import get_db, RequirePermission
from models.perfil import PerfilModel, PerfilPermissaoModel

router = APIRouter(prefix="/api/perfis", tags=["Perfis e Permissoes"])

# Schemas
class PermissaoSchema(BaseModel):
    modulo: str
    pode_visualizar: bool = False
    pode_criar: bool = False
    pode_editar: bool = False
    pode_excluir: bool = False

class PerfilCreateSchema(BaseModel):
    nome: str
    descricao: str = None
    permissoes: List[PermissaoSchema] = []

class PerfilResponseSchema(BaseModel):
    id: int
    nome: str
    descricao: str = None
    is_system: bool
    permissoes: List[PermissaoSchema] = []

    class Config:
        orm_mode = True

# Rotas
@router.get("/", response_model=List[PerfilResponseSchema], dependencies=[Depends(RequirePermission("usuarios_e_perfis", "visualizar"))])
def listar_perfis(db: Session = Depends(get_db)):
    return db.query(PerfilModel).all()

@router.post("/", response_model=PerfilResponseSchema, dependencies=[Depends(RequirePermission("usuarios_e_perfis", "criar"))])
def criar_perfil(body: PerfilCreateSchema, db: Session = Depends(get_db)):
    if db.query(PerfilModel).filter(PerfilModel.nome == body.nome).first():
        raise HTTPException(status_code=400, detail="Perfil já existe com este nome.")
        
    novo_perfil = PerfilModel(nome=body.nome, descricao=body.descricao)
    db.add(novo_perfil)
    db.flush()
    
    for perm in body.permissoes:
        db.add(PerfilPermissaoModel(
            perfil_id=novo_perfil.id,
            modulo=perm.modulo,
            pode_visualizar=perm.pode_visualizar,
            pode_criar=perm.pode_criar,
            pode_editar=perm.pode_editar,
            pode_excluir=perm.pode_excluir
        ))
    db.commit()
    db.refresh(novo_perfil)
    return novo_perfil

@router.put("/{id_perfil}", response_model=PerfilResponseSchema, dependencies=[Depends(RequirePermission("usuarios_e_perfis", "editar"))])
def atualizar_perfil(id_perfil: int, body: PerfilCreateSchema, db: Session = Depends(get_db)):
    perfil = db.query(PerfilModel).filter(PerfilModel.id == id_perfil).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    
    # Se for sistema, talvez nao deixar mudar o nome, mas as permissoes sim.
    if not perfil.is_system:
        perfil.nome = body.nome
    perfil.descricao = body.descricao
    
    # Limpa as velhas e bota as novas
    db.query(PerfilPermissaoModel).filter(PerfilPermissaoModel.perfil_id == id_perfil).delete()
    
    for perm in body.permissoes:
        db.add(PerfilPermissaoModel(
            perfil_id=perfil.id,
            modulo=perm.modulo,
            pode_visualizar=perm.pode_visualizar,
            pode_criar=perm.pode_criar,
            pode_editar=perm.pode_editar,
            pode_excluir=perm.pode_excluir
        ))
    db.commit()
    db.refresh(perfil)
    return perfil

@router.delete("/{id_perfil}", dependencies=[Depends(RequirePermission("usuarios_e_perfis", "excluir"))])
def excluir_perfil(id_perfil: int, db: Session = Depends(get_db)):
    perfil = db.query(PerfilModel).filter(PerfilModel.id == id_perfil).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    if perfil.is_system:
        raise HTTPException(status_code=400, detail="Perfis de sistema não podem ser excluídos.")
        
    # Verificar se ha usuarios usando
    from models.usuario import UsuarioModel
    if db.query(UsuarioModel).filter(UsuarioModel.perfil_id == id_perfil).first():
        raise HTTPException(status_code=400, detail="Há usuários vinculados a este perfil. Remova-os primeiro.")
        
    db.delete(perfil)
    db.commit()
    return {"ok": True}
