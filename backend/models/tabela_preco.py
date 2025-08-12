from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime
from database import Base
from datetime import datetime

class TabelaPreco(Base):
    __tablename__ = 'tb_tabela_preco'  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True)
    nome_tabela = Column(String, nullable=False)
    validade_inicio = Column(Date, nullable=False)
    validade_fim = Column(Date, nullable=False)
    fornecedor = Column(String, nullable=False)
    cliente = Column(String, nullable=False)

    codigo_tabela = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    embalagem = Column(String, nullable=True)
    peso_liquido = Column(Float, nullable=True)
    peso_bruto = Column(Float, nullable=True)
    valor = Column(Float, nullable=False)
    comissao_aplicada = Column(Float, default=0.0)
    ajuste_pagamento  = Column(Float, default=0.0)
    fator_comissao = Column(Float, nullable=True)
    plano_pagamento = Column(String, nullable=True)
    frete_percentual = Column(Float, nullable=True)
    frete_kg = Column(Float, nullable=True)
    valor_liquido = Column(Float, nullable=True)
    grupo = Column(String, nullable=True)
    departamento = Column(String, nullable=True)

    # Auditoria
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    editado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletado_em = Column(DateTime, nullable=True)