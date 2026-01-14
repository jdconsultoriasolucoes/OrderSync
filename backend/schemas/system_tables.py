from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# --- Condicao de Pagamento ---
class CondicaoPagamentoBase(BaseModel):
    prazo: Optional[str] = None
    descricao: Optional[str] = None
    custo: Optional[float] = None  # Recebe valor "percentual" (ex 5.0)

class CondicaoPagamentoCreate(CondicaoPagamentoBase):
    codigo_prazo: int
    ativo: bool = True

class CondicaoPagamentoUpdate(CondicaoPagamentoBase):
    ativo: Optional[bool] = None

class CondicaoPagamentoOut(CondicaoPagamentoBase):
    codigo_prazo: int
    ativo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    updated_by: Optional[str]

    class Config:
        from_attributes = True

# --- Desconto ---
class DescontoBase(BaseModel):
    fator_comissao: Optional[float] = None # Recebe valor "percentual"

class DescontoCreate(DescontoBase):
    id_desconto: int
    ativo: bool = True

class DescontoUpdate(DescontoBase):
    ativo: Optional[bool] = None

class DescontoOut(DescontoBase):
    id_desconto: int
    ativo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    updated_by: Optional[str]

    class Config:
        from_attributes = True

# --- Familia Produtos ---
class FamiliaProdutoBase(BaseModel):
    tipo: str
    familia: str
    marca: Optional[str] = None

class FamiliaProdutoCreate(FamiliaProdutoBase):
    ativo: bool = True

class FamiliaProdutoUpdate(FamiliaProdutoBase):
    ativo: Optional[bool] = None

class FamiliaProdutoOut(FamiliaProdutoBase):
    id: int
    ativo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    updated_by: Optional[str]

    class Config:
        from_attributes = True
