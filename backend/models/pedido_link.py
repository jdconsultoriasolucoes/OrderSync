from sqlalchemy import Column, String, Integer, Boolean, DateTime, func
from db import Base

class PedidoLink(Base):
    __tablename__ = "tb_pedido_link"

    code = Column(String(32), primary_key=True, index=True)
    tabela_id = Column(Integer, nullable=False)
    com_frete = Column(Boolean, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    uses = Column(Integer, default=0)
    max_uses = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
