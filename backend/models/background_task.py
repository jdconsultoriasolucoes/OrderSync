from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class BackgroundTaskModel(Base):
    __tablename__ = "tb_background_tasks"

    id = Column(Integer, primary_key=True, index=True)
    tipo_tarefa = Column(String(50), nullable=False)  # ex: 'ENVIO_EMAIL_CONFIRMACAO'
    referencia_id = Column(Integer, nullable=False)   # ex: id_pedido
    status = Column(String(20), nullable=False, default="PENDENTE") # PENDENTE, PROCESSANDO, CONCLUIDO, ERRO
    tentativas = Column(Integer, nullable=False, default=0)
    erro_msg = Column(Text, nullable=True)
    
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
