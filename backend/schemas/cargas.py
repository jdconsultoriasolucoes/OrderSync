from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .transporte import TransporteResponse 

# -------------- Carga Pedido (Itens) --------------

class CargaPedidoBase(BaseModel):
    numero_pedido: str
    ordem_carregamento: Optional[int] = None
    observacoes: Optional[str] = None

class CargaPedidoCreate(CargaPedidoBase):
    pass

class CargaPedidoResponse(CargaPedidoBase):
    id: int
    id_carga: int
    data_criacao: datetime

    class Config:
        from_attributes = True

# -------------- Carga (Cabeçalho) --------------

class CargaBase(BaseModel):
    nome_carga: Optional[str] = None
    numero_carga: Optional[str] = None
    id_transporte: Optional[int] = None
    data_carregamento: Optional[datetime] = None

class CargaCreate(CargaBase):
    pedidos: Optional[List[CargaPedidoCreate]] = []

class CargaUpdate(BaseModel):
    nome_carga: Optional[str] = None
    numero_carga: Optional[str] = None
    id_transporte: Optional[int] = None
    data_carregamento: Optional[datetime] = None

class CargaPedidoDetailUpdate(BaseModel):
    ordem_carregamento: Optional[int] = None
    observacoes: Optional[str] = None

class CargaResponse(CargaBase):
    id: int
    data_criacao: datetime
    data_update: datetime
    pedidos: List[CargaPedidoResponse] = []
    
    class Config:
        from_attributes = True
