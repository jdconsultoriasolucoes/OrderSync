from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RetiradaPedidoBase(BaseModel):
    numero_pedido: str
    observacoes: Optional[str] = None
    retirada_tipo: Optional[str] = None
    retirada_nome_terceiro: Optional[str] = None
    retirada_veiculo_modelo: Optional[str] = None
    retirada_veiculo_placa: Optional[str] = None
    retirada_horario: Optional[str] = None

class RetiradaPedidoCreate(RetiradaPedidoBase):
    pass

class RetiradaPedidoResponse(RetiradaPedidoBase):
    id: int
    id_retirada: int

    class Config:
        from_attributes = True

class RetiradaPedidoDetailUpdate(BaseModel):
    retirada_tipo: Optional[str] = None
    retirada_nome_terceiro: Optional[str] = None
    retirada_veiculo_modelo: Optional[str] = None
    retirada_veiculo_placa: Optional[str] = None
    retirada_horario: Optional[str] = None
    observacoes: Optional[str] = None

class RetiradaBase(BaseModel):
    nome_retirada: Optional[str] = None
    numero_retirada: Optional[str] = None
    data_retirada: Optional[datetime] = None

class RetiradaCreate(RetiradaBase):
    pedidos: Optional[List[RetiradaPedidoCreate]] = []

class RetiradaResponse(RetiradaBase):
    id: int
    is_historico: bool
    data_criacao: datetime
    data_update: datetime
    pedidos: List[RetiradaPedidoResponse] = []

    class Config:
        from_attributes = True
