from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import date


class TabelaPreco(BaseModel):
    # Identificadores
    id_tabela: Optional[int] = Field(None)
    id_linha: Optional[int] = Field(None)

    # Cabeçalho / metadados
    nome_tabela: str
    fornecedor: Optional[str] = None
    cliente: str
    
    # Produto (chave e descrição)
    codigo_tabela: str
    descricao: str
    embalagem: Optional[str] = None
    grupo: Optional[str] = None
    departamento: Optional[str] = None

    # Valores básicos
    peso_liquido: Optional[float] = None
    peso_bruto: Optional[float] = None
    valor: float
    desconto: Optional[float] = 0.0
    acrescimo: Optional[float] = 0.0
    fator_comissao: Optional[float] = None
    plano_pagamento: Optional[str] = None
    # Frete
    frete_percentual: Optional[float] = None
    frete_kg: Optional[float] = None

    # Totais (podem vir prontos do front)
    valor_liquido: Optional[float] = None
    valor_frete: Optional[float] = None
    valor_s_frete: Optional[float] = None

    # Fiscais
    ipi: Optional[float] = 0.0        
    iva_st: Optional[float] = 0.0       

    icms_st: Optional[bool] = Field(False, exclude=True)
    # --- Validadores ---
    @validator(
        "peso_liquido","peso_bruto","valor","desconto","acrescimo",
        "fator_comissao","frete_kg","ipi","iva_st"
    )
    def valida_positivos(cls, v, field):
        if v is not None and v < 0:
            raise ValueError(f"{field.name} deve ser um valor positivo.")
        return v

    @validator("frete_percentual", "iva_st")
    def valida_percentuais(cls, v, field):
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"{field.name} deve estar entre 0 e 100.")
        return v

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

class ProdutoCalculo(BaseModel):
    codigo_tabela: str
    descricao: str
    valor: float
    peso_liquido: Optional[float] = 0.0
    ipi: Optional[float] = 0.0
    iva_st: Optional[float] = 0.0
    tipo: Optional[str] = None
    
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
    cliente: str
    fornecedor: Optional[str] = None
    produtos: List[TabelaPreco]

StatusValidade = Literal["ok", "alerta", "expirada", "nao_definida"]

class ValidadeGlobalResp(BaseModel):
    validade_tabela: Optional[date] = None
    validade_tabela_br: Optional[str] = None 
    dias_restantes: Optional[int] = None
    status_validade: StatusValidade = "nao_definida"
    origem: Literal["max_ativos", "nao_definida"] = "nao_definida"


class ProdutoSalvar(BaseModel):
    codigo_tabela: str
    descricao: str
    embalagem: Optional[str] = None
    peso_liquido: Optional[float] = None
    valor: Optional[float] = None
    desconto: Optional[float] = 0.0
    acrescimo: Optional[float] = 0.0
    total_sem_frete: Optional[float] = 0.0
    # colunas novas que você disse que já existem
    valor_frete: Optional[float] = None
    valor_s_frete: Optional[float] = None
    plano_pagamento: Optional[str] = None
    # campos que às vezes vêm
    grupo: Optional[str] = None
    departamento: Optional[str] = None
    ipi: Optional[float] = 0.0
    iva_st: Optional[float] = 0.0
    class Config:
        extra = 'ignore'

class TabelaSalvar(BaseModel):
    nome_tabela: str
    cliente: str
    fornecedor: Optional[str] = None
    ramo_juridico: Optional[str] = None
    produtos: List[ProdutoSalvar]
    class Config:
        extra = 'ignore'    