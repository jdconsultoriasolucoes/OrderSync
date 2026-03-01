from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from database import Base

class IdempotencyKeyModel(Base):
    __tablename__ = "tb_idempotency_keys"

    chave = Column(String(100), primary_key=True, index=True)
    id_pedido = Column(Integer, nullable=False)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
