from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransporteBase(BaseModel):
    transportadora: str
    motorista: str
    veiculo_placa: str
    modelo: Optional[str] = None
    capacidade_kg: Optional[int] = None
    tipo_veiculo: Optional[str] = 'Proprio'

class TransporteCreate(TransporteBase):
    pass

class TransporteUpdate(BaseModel):
    transportadora: Optional[str] = None
    motorista: Optional[str] = None
    veiculo_placa: Optional[str] = None
    modelo: Optional[str] = None
    capacidade_kg: Optional[int] = None
    tipo_veiculo: Optional[str] = None
    data_desativacao: Optional[datetime] = None

class TransporteResponse(TransporteBase):
    id: int
    data_criacao: datetime
    data_update: datetime
    data_desativacao: Optional[datetime] = None

    class Config:
        from_attributes = True
