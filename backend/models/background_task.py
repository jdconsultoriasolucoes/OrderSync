from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class BackgroundTaskModel(Base):
    __tablename__ = "tb_background_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    tipo_tarefa = Column(String(50), nullable=False)   # ex: 'GERACAO_XML', 'RECALCULO_MASSIVO', 'ENVIO_EMAIL_CONFIRMACAO'
    referencia_id = Column(Integer, nullable=True)     # ex: id_pedido
    status = Column(String(20), nullable=False, default="PENDENTE")            # PENDENTE, PROCESSANDO, CONCLUIDO, ERRO
    tentativas = Column(Integer, nullable=False, default=0)
    erro_msg = Column(Text, nullable=True)
    
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    concluido_em = Column(DateTime, nullable=True)
    
    # Progresso e Mensagem (Recalculo Massivo)
    progresso = Column(Integer, default=0)
    total_passos = Column(Integer, default=0)
    mensagem_status = Column(Text, nullable=True)
    
    # Caso precise guardar output (ex: json, log de erro)
    resultado = Column(JSON, nullable=True)
    erro = Column(Text, nullable=True)
    
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
