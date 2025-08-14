from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date


class TabelaPreco(BaseModel):
    id_tabela: Optional[int] = Field(None, description="ID da tabela de preço")
    id_linha: Optional[int] = Field(None, description="ID interno da tabela de preço")

    # Dados principais
    nome_tabela: str = Field(..., description="Nome da tabela de preços")
    validade_inicio: date = Field(..., description="Data de início da validade")
    validade_fim: date = Field(..., description="Data de fim da validade")
    fornecedor: str = Field(..., description="Nome do fornecedor")
    cliente: str = Field(..., description="Código ou nome do cliente associado")

    # Dados do produto
    codigo_tabela: str
    descricao: str
    embalagem: Optional[str] = None
    peso_liquido: Optional[float] = None
    peso_bruto: Optional[float] = None
    valor: float
    desconto: Optional[float] = 0.0
    acrescimo: Optional[float] = 0.0
    fator_comissao: Optional[float] = None
    plano_pagamento: Optional[str] = None
    frete_percentual: Optional[float] = None
    frete_kg: Optional[float] = None
    valor_liquido: Optional[float] = None
    grupo: Optional[str] = None
    departamento: Optional[str] = None

    @validator("peso_liquido", "peso_bruto", "valor", "desconto", "acrescimo", "fator_comissao",
               "frete_percentual", "frete_kg", "valor_liquido")
    def valida_positivos(cls, v, field):
        if v is not None and v < 0:
            raise ValueError(f"{field.name} deve ser um valor positivo.")
        return v
    
    class Config:
            orm_mode = True

class ProdutoCalculo(BaseModel):
    codigo_tabela: str
    descricao: str
    valor: float
    peso_liquido: Optional[float] = 0.0

class ParametrosCalculo(BaseModel):
    produtos: List[ProdutoCalculo]
    frete_unitario : float
    fator_comissao: float
    acrescimo_pagamento: float

class ProdutoCalculado(ProdutoCalculo):
    frete_kg: float
    comissao_aplicada: float
    ajuste_pagamento: float
    valor_liquido: float          


class TabelaPrecoCompleta(BaseModel):
    nome_tabela: str
    validade_inicio: date
    validade_fim: date
    cliente: str
    fornecedor: str
    produtos: List[TabelaPreco]
