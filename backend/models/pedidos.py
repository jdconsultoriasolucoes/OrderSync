from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Date, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base
from models.tabela_preco import TabelaPreco

class PedidoModel(Base):
    __tablename__ = "tb_pedidos"

    id_pedido = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    # Cliente info (denormalized or loose link)
    codigo_cliente = Column(String)
    cliente = Column(String) # Nome do cliente
    contato_nome = Column(String)
    contato_email = Column(String)
    contato_fone = Column(String)

    # Tabela de Preco
    tabela_preco_id = Column(Integer, ForeignKey("tb_tabela_preco.id_tabela"))
    
    # Detalhes do Pedido
    fornecedor = Column(String)
    status = Column(String, default="ABERTO")
    
    # Valores e Frete
    usar_valor_com_frete = Column(Boolean, default=False)
    peso_total_kg = Column(Float, default=0.0)
    frete_total = Column(Float, default=0.0)
    total_pedido = Column(Float, default=0.0)

    # Validade
    validade_ate = Column(Date)
    validade_dias = Column(Integer)
    data_prevista = Column(Date)

    # Workflow timestamps
    confirmado_em = Column(DateTime(timezone=True))
    cancelado_em = Column(DateTime(timezone=True))
    cancelado_motivo = Column(String)

    # Link Publico
    link_url = Column(String)
    link_status = Column(String)
    link_enviado_em = Column(DateTime(timezone=True))
    link_primeiro_acesso_em = Column(DateTime(timezone=True))

    observacoes = Column(Text)

    # Relationships
    tabela_preco = relationship("TabelaPreco", backref="pedidos", foreign_keys=[tabela_preco_id], primaryjoin="remote(TabelaPreco.id_tabela)==foreign(PedidoModel.tabela_preco_id)", uselist=True, viewonly=True)
    itens = relationship("PedidoItemModel", back_populates="pedido", cascade="all, delete-orphan")


class PedidoItemModel(Base):
    __tablename__ = "tb_pedidos_itens"

    id_item = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("tb_pedidos.id_pedido"))

    codigo = Column(String)
    nome = Column(String)
    embalagem = Column(String)
    quantidade = Column(Float)
    
    # Precos snapshot
    preco_unit = Column(Float)          # Base price
    preco_unit_frt = Column(Float)      # With freight
    
    subtotal_sem_f = Column(Float)
    subtotal_com_f = Column(Float)

    pedido = relationship("PedidoModel", back_populates="itens")
