from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, func
from db import Base

class PedidoLink(Base):
    __tablename__ = "tb_pedido_link"

    code = Column(String(32), primary_key=True, index=True)
    tabela_id = Column(Integer, nullable=False)
    com_frete = Column(Boolean, nullable=False)
    data_prevista = Column(Date, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    uses = Column(Integer, default=0)
    max_uses = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    codigo_cliente  = Column(String(80), nullable=True)
    first_access_at = Column(DateTime(timezone=True), nullable=True)
    last_access_at  = Column(DateTime(timezone=True), nullable=True)