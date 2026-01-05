
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Sequence, DateTime, func
from database import Base

class UsuarioModel(Base):
    __tablename__ = "t_usuario"

    id = Column(BigInteger, Sequence('usuario_id_seq'), primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    funcao = Column(String, default="vendedor") # admin, gerente, vendedor
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    criado_por = Column(String, nullable=True)
    reset_senha_obrigatorio = Column(Boolean, default=False)
