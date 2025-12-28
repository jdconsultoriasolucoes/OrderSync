
from pydantic import BaseModel
from typing import Optional

class UsuarioBase(BaseModel):
    email: str
    nome: Optional[str] = None
    funcao: str = "vendedor"
    ativo: bool = True

class UsuarioCreate(UsuarioBase):
    senha: str

from datetime import datetime

class UsuarioLogin(BaseModel):
    email: str
    senha: str

class UsuarioPublic(BaseModel):
    id: int
    nome: str
    email: str
    funcao: str
    ativo: bool
    data_criacao: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    funcao: str
    nome: str

class UsuarioUpdateSenha(BaseModel):
    senha_antiga: str
    senha_nova: str

class UsuarioResetSenha(BaseModel):
    senha_nova: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    funcao: Optional[str] = None
    ativo: Optional[bool] = None
