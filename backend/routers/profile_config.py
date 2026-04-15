"""
Router para configuração do perfil do representante (Profile Config).
Visível para todos os usuários autenticados, editável somente por admin.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import SessionLocal
from models.profile_config import ProfileConfigModel
from models.usuario import UsuarioModel
from core.deps import get_current_user
import logging

logger = logging.getLogger("ordersync.routers.profile_config")

router = APIRouter(prefix="/profile-config", tags=["Profile Config"])


class ProfileConfigSchema(BaseModel):
    codigo_representante: Optional[str] = None
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    endereco: Optional[str] = None


@router.get("/", response_model=ProfileConfigSchema)
def get_profile_config(current_user: UsuarioModel = Depends(get_current_user)):
    """Retorna a configuração global do representante. Acessível a qualquer usuário autenticado."""
    with SessionLocal() as db:
        config = db.query(ProfileConfigModel).first()
        if not config:
            # Cria registro default se não existir
            config = ProfileConfigModel(
                codigo_representante="",
                cnpj="",
                razao_social="",
                endereco=""
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return ProfileConfigSchema(
            codigo_representante=config.codigo_representante or "",
            cnpj=config.cnpj or "",
            razao_social=config.razao_social or "",
            endereco=config.endereco or ""
        )


@router.put("/", response_model=ProfileConfigSchema)
def update_profile_config(
    dados: ProfileConfigSchema,
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Atualiza a configuração do representante. Somente admin pode editar."""
    if current_user.funcao != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar o perfil do representante.")

    with SessionLocal() as db:
        config = db.query(ProfileConfigModel).first()
        if not config:
            config = ProfileConfigModel()
            db.add(config)
        
        if dados.codigo_representante is not None:
            config.codigo_representante = dados.codigo_representante
        if dados.cnpj is not None:
            config.cnpj = dados.cnpj
        if dados.razao_social is not None:
            config.razao_social = dados.razao_social
        if dados.endereco is not None:
            config.endereco = dados.endereco
        
        db.commit()
        db.refresh(config)
        
        return ProfileConfigSchema(
            codigo_representante=config.codigo_representante or "",
            cnpj=config.cnpj or "",
            razao_social=config.razao_social or "",
            endereco=config.endereco or ""
        )
