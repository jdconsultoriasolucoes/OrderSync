
class UsuarioAdminResetSenha(BaseModel):
    senha_nova: str

    @validator('senha_nova')
    def valid_senha_nova(cls, v):
        return validate_strength(v)
