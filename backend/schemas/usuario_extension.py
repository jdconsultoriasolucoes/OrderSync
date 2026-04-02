
from pydantic import BaseModel, field_validator
from backend.schemas.usuario import validate_strength

class UsuarioAdminResetSenha(BaseModel):
    senha_nova: str

    @field_validator('senha_nova')
    @classmethod
    def valid_senha_nova(cls, v):
        return validate_strength(v)
