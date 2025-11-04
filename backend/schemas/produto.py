# schemas/produto_v2.py
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import date

# ---------- Imposto ----------
class ImpostoV2Base(BaseModel):
    ipi: Optional[float] = None
    icms: Optional[float] = None
    iva_st: Optional[float] = Field(None, description="Substituição Tributária (%)")
    cbs: Optional[float] = None
    ibs: Optional[float] = None

class ImpostoV2Create(ImpostoV2Base):
    pass

class ImpostoV2Out(ImpostoV2Base):
    id: int
    class Config:
        from_attributes = True

# ---------- Produto ----------
class ProdutoV2Base(BaseModel):
    codigo_supra: str
    status_produto: str
    nome_produto: str

    tipo_giro: Optional[str] = None
    estoque_disponivel: Optional[int] = None
    unidade: Optional[str] = None
    peso: Optional[float] = None
    peso_bruto: Optional[float] = None
    estoque_ideal: Optional[int] = None
    embalagem_venda: Optional[str] = None
    unidade_embalagem: Optional[int] = None
    codigo_ean: Optional[str] = None
    codigo_embalagem: Optional[str] = None
    ncm: Optional[str] = None
    fornecedor: Optional[str] = None
    filhos: Optional[int] = None
    familia: Optional[int] = None

    preco: Optional[float] = None                      # Valor Tabela Atual (oficial)
    preco_tonelada: Optional[float] = None
    validade_tabela: Optional[date] = None

    desconto_valor_tonelada: Optional[float] = None    # R$/t
    data_desconto_inicio: Optional[date] = None
    data_desconto_fim: Optional[date] = None

    @field_validator("preco", "preco_tonelada", "desconto_valor_tonelada")
    @classmethod
    def _nao_negativo(cls, v):
        if v is not None and v < 0:
            raise ValueError("valor não pode ser negativo")
        return v

class ProdutoV2Create(ProdutoV2Base):
    pass

class ProdutoV2Update(ProdutoV2Base):
    # tudo opcional em PATCH
    codigo_supra: Optional[str] = None
    status_produto: Optional[str] = None
    nome_produto: Optional[str] = None

    @field_validator("data_desconto_fim")
    @classmethod
    def _datas_coesas(cls, v, info):
        ini = info.data.get("data_desconto_inicio")
        fim = v
        # regra: se preencher um, tem que preencher os dois; e ini <= fim
        if (ini and not fim) or (fim and not ini):
            raise ValueError("preencha data_desconto_inicio e data_desconto_fim juntos")
        if ini and fim and ini > fim:
            raise ValueError("data_desconto_inicio deve ser <= data_desconto_fim")
        return v

class ProdutoV2Out(ProdutoV2Base):
    id: int

    # snapshots (lidos da tabela)
    unidade_anterior: Optional[str] = None
    preco_anterior: Optional[float] = None
    preco_tonelada_anterior: Optional[float] = None
    validade_tabela_anterior: Optional[date] = None

    # calculados / flags
    preco_final: Optional[float] = None
    reajuste_percentual: Optional[float] = None
    vigencia_ativa: Optional[bool] = None

    # impostos (1–1)
    imposto: Optional[ImpostoV2Out] = None

    class Config:
        from_attributes = True
