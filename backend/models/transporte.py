from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class TransporteModel(Base):
    __tablename__ = "tb_transporte"

    id = Column(Integer, primary_key=True, index=True)
    transportadora = Column(String, nullable=False)
    motorista = Column(String, nullable=False)
    veiculo_placa = Column(String, nullable=False)
    modelo = Column(String, nullable=True)
    capacidade_kg = Column(Integer, nullable=True)
    tipo_veiculo = Column(String, nullable=True) # [Ex: 'Proprio', 'Terceiro']
    
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_desativacao = Column(DateTime, nullable=True)
