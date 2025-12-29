from pydantic import BaseModel, Field, field_validator, ValidationInfo
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
    codigo_produto_supra: str
    descricao_produto: Optional[str]
    embalagem: Optional[str] = None
    grupo: Optional[str] = None
    departamento: Optional[str] = None

    # Valores básicos
    peso_liquido: Optional[float] = None
    valor_produto: float
    desconto: Optional[float] = 0.0
    acrescimo: Optional[float] = 0.0
    descricao_fator_comissao: Optional[str] = None
    codigo_plano_pagamento: Optional[str] = None
    markup: Optional[float] = 0.0
    # Frete
    valor_frete_aplicado: Optional[float] = None
    frete_kg: Optional[float] = None

    # Totais (podem vir prontos do front)
    valor_liquido: Optional[float] = None
    valor_frete: Optional[float] = None
    valor_s_frete: Optional[float] = None

    # Fiscais
    ipi: Optional[float] = 0.0        
    iva_st: Optional[float] = 0.0       

    icms_st: Optional[float] = 0.0
    # --- Validadores ---
    @field_validator(
        "peso_liquido", "valor_produto", "comissao_aplicada", "ajuste_pagamento",
    "frete_kg", "ipi", "iva_st", "icms_st",
          
          check_fields=False)
    @classmethod
    def valida_positivos(cls, v, info: ValidationInfo):
        if v is None:
            return v
        try:
            val = float(v)
        except (TypeError, ValueError):
            # In V2 we can skip accessing field name or use info.field_name if needed
            pass
        return v
   
    class Config:
        from_attributes = True
        str_strip_whitespace = True


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
    calcula_st: bool = False
StatusValidade = Literal["ok", "alerta", "expirada", "nao_definida"]

class ValidadeGlobalResp(BaseModel):
    validade_tabela: Optional[date] = None
    validade_tabela_br: Optional[str] = None 
    dias_restantes: Optional[int] = None
    status_validade: StatusValidade = "nao_definida"
    origem: Literal["max_ativos", "nao_definida"] = "nao_definida"


class ProdutoSalvar(BaseModel):
    # RENOMES
    codigo_produto_supra: str          # was: codigo_tabela
    descricao_produto: str             # was: descricao
    valor_produto: Optional[float]     # was: valor
    codigo_plano_pagamento: Optional[str]  # was: plano_pagamento
    valor_frete_aplicado: Optional[float]  # was: frete_percentual
    descricao_fator_comissao: Optional[str]# was: fator_comissao
    markup: Optional[float] = 0.0
    valor_final_markup: Optional[float] = 0.0 # NOVO
    valor_s_frete_markup: Optional[float] = 0.0 # NOVO

    # JÁ EXISTENTES (mantém nomes atuais)
    embalagem: Optional[str] = None
    peso_liquido: Optional[float] = None
    comissao_aplicada: Optional[float] = 0.0
    ajuste_pagamento: Optional[float] = 0.0
    frete_kg: Optional[float] = None

    # Totais (armazenar como vem)
    valor_frete: Optional[float] = None
    valor_s_frete: Optional[float] = None

    # Classificações e fiscais (armazenar como vem)
    grupo: Optional[str] = None
    departamento: Optional[str] = None
    ipi: Optional[float] = 0.0
    icms_st: Optional[float] = 0.0
    iva_st: Optional[float] = 0.0

    class Config:
        extra = "ignore"

class TabelaSalvar(BaseModel):
    # Cabeçalho (confirmar se já tinha; se não, adicionar)
    id_tabela: Optional[int] = None
    nome_tabela: str
    cliente: str
    fornecedor: Optional[str] = None

    # NOVOS
    codigo_cliente: Optional[str] = None
    criacao_usuario: Optional[str] = None
    alteracao_usuario: Optional[str] = None

    # Se o frete/kg vier no header e você replicar nos itens
    frete_kg: Optional[float] = None

    calcula_st: bool = False
    
    produtos: List[ProdutoSalvar]

    class Config:
        extra = "ignore"
