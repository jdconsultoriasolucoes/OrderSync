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
    valor_retira: float
    valor_entrega: float


class PedidoPdf(BaseModel):
    id_pedido: int
    codigo_cliente: str
    cliente: str
    nome_fantasia: str = "Sem Nome Fantasia"  # 👈 novo campo
    data_pedido: Optional[datetime] = None
    data_entrega_ou_retirada: Optional[datetime] = None
    frete_total: float = 0.0
    total_peso_bruto: float = 0.0
    total_valor: float = 0.0
    observacoes: str = ""
    itens: List[PedidoPdfItem] = [] 
