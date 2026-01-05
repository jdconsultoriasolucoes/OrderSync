
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re

def validate_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError('A senha deve ter no mínimo 8 caracteres')
    if not re.search(r"[A-Z]", v):
        raise ValueError('A senha deve ter pelo menos uma letra maiúscula')
    if not re.search(r"[a-z]", v):
        raise ValueError('A senha deve ter pelo menos uma letra minúscula')
    if not re.search(r"[0-9]", v):
        raise ValueError('A senha deve ter pelo menos um número')
    if not re.search(r"[\W_]", v):
        raise ValueError('A senha deve ter pelo menos um caractere especial (ex: @, #, $, !)')
    return v

class UsuarioBase(BaseModel):
    email: str
    nome: Optional[str] = None
    funcao: str = "vendedor"
    ativo: bool = True

class UsuarioCreate(UsuarioBase):
    senha: str

    @validator('senha')
    def valid_senha(cls, v):
        return validate_strength(v)

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

    @validator('senha_nova')
    def valid_senha_nova(cls, v):
        return validate_strength(v)

class UsuarioResetSenha(BaseModel):
    token: str
    senha_nova: str

    @validator('senha_nova')
    def valid_senha_nova(cls, v):
        return validate_strength(v)

class UsuarioForgotPassword(BaseModel):
    email: str

class UsuarioChangePassword(BaseModel):
    senha_atual: str
    nova_senha: str

    @validator('nova_senha')
    def valid_nova_senha(cls, v):
        return validate_strength(v)

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    funcao: Optional[str] = None
    ativo: Optional[bool] = None
