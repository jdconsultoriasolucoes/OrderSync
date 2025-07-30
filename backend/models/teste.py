# backend/models/teste.py
from sqlalchemy import Column, Integer, String
from database import Base

class Teste(Base):
    __tablename__ = "tb_teste"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)