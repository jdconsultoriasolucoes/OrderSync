from sqlalchemy import Column, Integer, String, Float
from database import Base

class CanalVendaModel(Base):
    __tablename__ = "tb_canal_venda"

    Id = Column("Id", Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column("tipo", String)
    linha = Column("linha", String)

class CidadeSupervisorModel(Base):
    __tablename__ = "tb_cidade_supervisor"

    codigo = Column("codigo", Integer, primary_key=True, index=True, autoincrement=True)
    numero_supervisor_insumos = Column("numero_supervisor_insumos", Float)
    numero_supervisor_pet = Column("numero_supervisor_pet", Float)
    nome_supervisor_pet = Column("nome_supervisor_pet", String)
    nome_supervisor_insumos = Column("nome_supervisor_insumos", String)
    cidades = Column("cidades", String)
    uf = Column("uf", String)

class MunicipioRotaModel(Base):
    __tablename__ = "tb_municipio_rota"

    id = Column("id", Integer, primary_key=True, index=True, autoincrement=True)
    rota = Column("rota", Integer)
    municipio = Column("municipio", String)
    km = Column("km", String)

class ReferenciasModel(Base):
    __tablename__ = "tb_referencias"

    codigo = Column("codigo", Integer, primary_key=True, index=True, autoincrement=True)
    empresa = Column("empresa", String)
    cidade = Column("cidade", String)
    telefone = Column("telefone", String)
    contato = Column("contato", String)

class SupervisoresModel(Base):
    __tablename__ = "tb_supervisores"

    id = Column("id", Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column("codigo", Float)
    supervisores = Column("supervisores", String)
    tipo = Column("tipo", String)
    telefone = Column("telefone", String)
    email = Column("e-mail", String)  # Note o mapeamento da coluna 'e-mail'

class PlantelAnimalModel(Base):
    __tablename__ = "tb_plantel_animais"

    id = Column("id", Integer, primary_key=True, index=True, autoincrement=True)
    plantel_animais = Column("plantel_animais", String)

