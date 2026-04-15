
from sqlalchemy import Column, Integer, String, BigInteger, Sequence, DateTime, func
from database import Base

class ProfileConfigModel(Base):
    """
    Configuração global do representante/empresa.
    Apenas 1 registro por sistema (singleton).
    Visível para todos, editável somente por admin.
    """
    __tablename__ = "t_profile_config"

    id = Column(BigInteger, Sequence('profile_config_id_seq'), primary_key=True, index=True)
    codigo_representante = Column(String, nullable=True)
    cnpj = Column(String, nullable=True)
    razao_social = Column(String, nullable=True)
    endereco = Column(String, nullable=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
