from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class RetiradaModel(Base):
    __tablename__ = "tb_retiradas"

    id = Column(Integer, primary_key=True, index=True)
    nome_retirada = Column(String(255), nullable=True)
    numero_retirada = Column(String(100), unique=True, index=True, nullable=True)
    data_retirada = Column(DateTime, nullable=True)
    is_historico = Column(Boolean, default=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pedidos = relationship("RetiradaPedidoModel", back_populates="retirada", cascade="all, delete-orphan")

class RetiradaPedidoModel(Base):
    __tablename__ = "tb_retiradas_pedidos"

    id = Column(Integer, primary_key=True, index=True)
    id_retirada = Column(Integer, ForeignKey("tb_retiradas.id", ondelete="CASCADE"), nullable=False)
    numero_pedido = Column(String(100), index=True, nullable=True)
    observacoes = Column(Text, nullable=True)
    retirada_tipo = Column(String(50), nullable=True)
    retirada_nome_terceiro = Column(String(255), nullable=True)
    retirada_veiculo_modelo = Column(String(255), nullable=True)
    retirada_veiculo_placa = Column(String(50), nullable=True)
    retirada_horario = Column(String(50), nullable=True)

    retirada = relationship("RetiradaModel", back_populates="pedidos")
