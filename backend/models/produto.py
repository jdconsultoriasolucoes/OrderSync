# models/produto_v2.py
from sqlalchemy import (
    Column, BigInteger, Integer, Text, Numeric, Date, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# ajuste este import conforme seu projeto:
from database import Base # ou: from db.session import Base


class ProdutoV2(Base):
    __tablename__ = "t_cadastro_produto_v2"

    id = Column(BigInteger, primary_key=True)

    # Identificação / status
    codigo_supra = Column(Text, nullable=False)          # Código
    status_produto = Column(Text, nullable=False)        # Status
    nome_produto = Column(Text, nullable=False)          # Descrição
    tipo_giro = Column(Text)
    tipo = Column(Text)                                  # 'INSUMOS' ou 'PET'

    # Estoque / unidade / pesos
    estoque_disponivel = Column(Integer)
    unidade = Column(Text)                               # Unidade de venda (atual)
    unidade_anterior = Column(Text)                      # Snapshot unidade anterior
    peso = Column(Numeric(12, 3))                        # Peso Líquido
    peso_bruto = Column(Numeric(12, 3))
    estoque_ideal = Column(Integer)
    embalagem_venda = Column(Text)
    unidade_embalagem = Column(Integer)

    # Códigos / classificação
    codigo_ean = Column(Text)                            # EAN/GTIN
    codigo_embalagem = Column(Text)                      # GTIN da caixa
    ncm = Column(Text)                                   # NCM/SH (só leitura na tela)
    fornecedor = Column(Text)
    filhos = Column(Integer)                             # Filho nº (int)
    familia = Column(Text)                               # Nome da Família (era ID, mas agora é Texto vindo do PDF)
    marca = Column(Text)                                 # Marca do produto

    # Preços e vigências
    preco = Column(Numeric(14, 4))                       # Valor Tabela Atual (oficial)
    preco_anterior = Column(Numeric(14, 4))              # Snapshot quando preço muda
    preco_tonelada = Column(Numeric(14, 4))
    preco_tonelada_anterior = Column(Numeric(14, 4))     # Snapshot quando preço_tonelada muda
    validade_tabela = Column(Date)                       # "Validade da Tabela Atual a partir de"
    validade_tabela_anterior = Column(Date)              # Snapshot (D-1) quando muda a validade

    # Desconto por tonelada (R$/t) e período
    desconto_valor_tonelada = Column(Numeric(14, 4))
    data_desconto_inicio = Column(Date)
    data_desconto_fim = Column(Date)

    # Calculado pela trigger
    preco_final = Column(Numeric(14, 4))                 # max(preco_tonelada - desconto_aplicável, 0)

    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    criado_por = Column(Text, nullable=True)
    atualizado_por = Column(Text, nullable=True)

    # Relação 1–1 com impostos
    imposto = relationship("ImpostoV2", back_populates="produto", uselist=False)

    __table_args__ = (
        UniqueConstraint("codigo_supra", name="ux_produto_v2_codigo"),
    )


class ImpostoV2(Base):
    __tablename__ = "t_imposto_v2"

    id = Column(BigInteger, primary_key=True)
    produto_id = Column(BigInteger, ForeignKey("t_cadastro_produto_v2.id", ondelete="CASCADE"),
                        unique=True, nullable=False)

    ipi = Column(Numeric(10, 4))
    icms = Column(Numeric(10, 4))
    iva_st = Column(Numeric(10, 4))                       # Substituição Tributária (%)
    cbs = Column(Numeric(10, 4))
    ibs = Column(Numeric(10, 4))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    produto = relationship("ProdutoV2", back_populates="imposto")
