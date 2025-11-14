# models/pedido_pdf.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class PedidoPdfItem(BaseModel):
    codigo: str
    produto: str
    embalagem: Optional[str] = None
    quantidade: float
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    valor_retira: float      # pode ser unitário ou subtotal, você escolhe
    valor_entrega: float     # idem


class PedidoPdf(BaseModel):
    id_pedido: int
    codigo_cliente: Optional[str] = None
    cliente: str
    data_pedido: datetime
    data_entrega_ou_retirada: Optional[date] = None
    frete_total: float
    total_peso_bruto: float
    total_valor: float
    itens: List[PedidoPdfItem]
