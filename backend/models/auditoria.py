from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class LogisticaAuditoriaModel(Base):
    __tablename__ = "tb_logistica_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    tipo_operacao = Column(String(50), nullable=False) # 'CARGA' ou 'RETIRADA'
    id_original = Column(Integer, nullable=False, index=True)
    numero_identificador = Column(String(100), nullable=True) # Ex: numero_carga ou numero_retirada
    data_criacao_original = Column(DateTime, nullable=True)
    data_finalizacao = Column(DateTime, default=datetime.utcnow)
    usuario_responsavel = Column(String(255), nullable=True) # Nome ou email de quem finalizou
    snapshot_dados = Column(Text, nullable=True) # JSON com todos os dados congelados
