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
    markup: Optional[float] = 0.0
    valor_final_markup: Optional[float] = 0.0
    valor_s_frete_markup: Optional[float] = 0.0


class PedidoPdf(BaseModel):
    id_pedido: int
    codigo_cliente: Optional[str]
    cliente: str

    # NOVOS
    nome_fantasia: Optional[str] = None
    frete_kg: Optional[float] = None
    validade_tabela: Optional[str] = "Não se aplica"

    data_pedido: Optional[datetime]
    data_entrega_ou_retirada: Optional[datetime]
    frete_total: float
    total_peso_bruto: float
    total_peso_liquido: float # NOVO
    total_valor: float
    observacoes: Optional[str] = None
    itens: List[PedidoPdfItem]
