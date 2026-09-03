from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base

class PerfilModel(Base):
    __tablename__ = "tb_perfis"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    descricao = Column(String, nullable=True)
    is_system = Column(Boolean, default=False) # true para "admin" etc, impedindo exclusao

    permissoes = relationship("PerfilPermissaoModel", back_populates="perfil", cascade="all, delete-orphan")

class PerfilPermissaoModel(Base):
    __tablename__ = "tb_perfil_permissoes"

    id = Column(Integer, primary_key=True, index=True)
    perfil_id = Column(Integer, ForeignKey("tb_perfis.id", ondelete="CASCADE"), nullable=False)
    modulo = Column(String, nullable=False)
    
    pode_visualizar = Column(Boolean, default=False)
    pode_criar = Column(Boolean, default=False)
    pode_editar = Column(Boolean, default=False)
    pode_excluir = Column(Boolean, default=False)

    perfil = relationship("PerfilModel", back_populates="permissoes")
