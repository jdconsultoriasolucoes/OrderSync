from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, Numeric, UniqueConstraint
from database import Base
from datetime import datetime

class TabelaPreco(Base):
    __tablename__ = "tb_tabela_preco"
   
    id_linha = Column(Integer, primary_key=True, autoincrement=True)
    id_tabela = Column(Integer, nullable=False, index=True)
    nome_tabela = Column(Text, nullable=False)
    fornecedor = Column(Text, nullable=False)
    codigo_cliente = Column(Text, nullable=True)
    cliente = Column(Text, nullable=False)

    codigo_produto_supra = Column(Text, nullable=False)
    descricao_produto = Column(Text, nullable=False)
    embalagem = Column(Text, nullable=False)

    peso_liquido = Column(Numeric(9, 3), nullable=False)

    valor_produto = Column(Numeric(14, 2), nullable=False)
    comissao_aplicada = Column(Numeric(9, 4), nullable=False, default=0)
    ajuste_pagamento = Column(Numeric(14, 2), nullable=False, default=0)
    descricao_fator_comissao = Column(Text, nullable=False)
    codigo_plano_pagamento = Column(Text, nullable=False)
    markup = Column(Numeric(9, 3), nullable=False, default=0) # Markup %
    valor_final_markup = Column(Numeric(14, 2), nullable=False, default=0) # Valor Final com Markup
    valor_s_frete_markup = Column(Numeric(14, 2), nullable=False, default=0) # Valor s/ Frete com Markup
    valor_frete_aplicado = Column(Numeric(14, 2), nullable=False, default=0)  # R$
    frete_kg = Column(Numeric(9, 3), nullable=False, default=0)

    # valor_liquido: NÃO persistir (a pedido)

    valor_frete = Column(Numeric(14, 2), nullable=False)
    valor_s_frete = Column(Numeric(14, 2), nullable=False)

    grupo = Column(Text, nullable=False)
    departamento = Column(Text, nullable=False)

    ipi = Column(Numeric(14, 2), nullable=False)      # R$
    icms_st = Column(Numeric(14, 2), nullable=False)  # R$
    iva_st = Column(Numeric(14, 2), nullable=False)   # R$

    calcula_st = Column(Boolean, nullable=False, default=False)
    
    ativo = Column(Boolean, nullable=False, default=True)

    criado_em = Column(DateTime, nullable=True)
    editado_em = Column(DateTime, nullable=True)
    deletado_em = Column(DateTime, nullable=True)

    criacao_usuario = Column(Text, nullable=True)
    alteracao_usuario = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("id_tabela", "codigo_produto_supra", name="uq_tabela_produto"),
    )