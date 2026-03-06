from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class CargaModel(Base):
    __tablename__ = "tb_cargas"

    id = Column(Integer, primary_key=True, index=True)
    numero_carga = Column(String, unique=True, index=True, nullable=False)
    id_transporte = Column(Integer, ForeignKey("tb_transporte.id"), nullable=True) # Ligação com transporte (Motorista/Veículo)
    data_carregamento = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    pedidos = relationship("CargaPedidoModel", back_populates="carga", cascade="all, delete-orphan")

class CargaPedidoModel(Base):
    """
    Tabela associativa/detalhe que vincula a Carga a vários Pedidos (Ordem de Carregamento)
    """
    __tablename__ = "tb_cargas_pedidos"

    id = Column(Integer, primary_key=True, index=True)
    id_carga = Column(Integer, ForeignKey("tb_cargas.id", ondelete="CASCADE"), nullable=False)
    numero_pedido = Column(String, nullable=False, index=True) # Referência ao pedido na "tb_pedidos"
    ordem_carregamento = Column(Integer, nullable=True)
    observacoes = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    carga = relationship("CargaModel", back_populates="pedidos")
