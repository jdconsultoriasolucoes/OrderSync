from sqlalchemy import Column, Integer, String
from database import Base

class Fornecedor(Base):
    __tablename__ = "t_fornecedor"

    id = Column(Integer, primary_key=True, index=True)
    nome_fornecedor = Column(String, nullable=False)
