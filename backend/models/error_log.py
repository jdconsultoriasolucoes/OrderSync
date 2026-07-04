from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from database import Base

class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=True)  # ID of user if logged in
    modulo = Column(String(255), index=True)      # Path or Module name
    status_code = Column(Integer)                 # 422, 500, etc
    mensagem = Column(Text, nullable=False)       # Translated friendly message or raw error
    payload = Column(JSON, nullable=True)         # Additional info, api response, etc
    data_hora = Column(DateTime(timezone=True), server_default=func.now(), index=True)
