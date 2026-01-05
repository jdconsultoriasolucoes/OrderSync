from pydantic import BaseModel
from typing import List, Optional

class ConfirmarItem(BaseModel):
    codigo: str
    descricao: str | None = None
    embalagem: str | None = None
    condicao_pagamento: str | None = None
    tabela_comissao: str | None = None 
    quantidade: int
    preco_unit: float | None = None
    preco_unit_com_frete: float | None = None
    peso_kg: float | None = None

class ConfirmarPedidoRequest(BaseModel):
    origin_code: str | None = None              
    usar_valor_com_frete: bool = True
    produtos: list[ConfirmarItem]
    observacao: str | None = None
    cliente: str | None = None                  
    validade_ate: str | None = None             
    data_retirada: str | None = None            
    validade_dias: int | None = None
    codigo_cliente: str | None = None
    link_url: str | None = None
