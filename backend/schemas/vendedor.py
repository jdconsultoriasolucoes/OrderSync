from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class VendedorBase(BaseModel):
    nome: str
    email: Optional[str] = None
    ativo: Optional[bool] = True

class VendedorCreate(VendedorBase):
    pass

class VendedorUpdate(VendedorBase):
    pass

class VendedorResponse(VendedorBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
