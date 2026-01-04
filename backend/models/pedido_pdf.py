from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PedidoPdfItem(BaseModel):
    codigo: str
    produto: str
    embalagem: Optional[str] = None
    quantidade: float
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    valor_retira: float
    valor_entrega: float


class PedidoPdf(BaseModel):
    id_pedido: int
    codigo_cliente: Optional[str]
    cliente: str

    # NOVOS
    nome_fantasia: Optional[str] = None
    frete_kg: Optional[float] = None
    validade_tabela: Optional[datetime] = None  # NEW

    data_pedido: Optional[datetime]
    data_entrega_ou_retirada: Optional[datetime]
    frete_total: float
    total_peso_bruto: float
    total_valor: float
    observacoes: Optional[str] = None
    itens: List[PedidoPdfItem]
