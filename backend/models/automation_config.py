from sqlalchemy import Column, Integer, String, Boolean, Time
from database import Base

class AutomationConfigModel(Base):
    __tablename__ = "tb_automation_config"

    id = Column(Integer, primary_key=True, index=True)
    
    # Prospecção Semanal
    prospeccao_ativa = Column(Boolean, default=False)
    prospeccao_dia_semana = Column(Integer, default=0) # 0 = Segunda, 1 = Terça...
    prospeccao_horario = Column(Time, nullable=True) # HH:MM:SS
    
    # Rastrear o último envio para não enviar duplicado no mesmo dia
    prospeccao_ultimo_envio = Column(String(20), nullable=True) # Ex: "2024-05-13" (data do envio)
