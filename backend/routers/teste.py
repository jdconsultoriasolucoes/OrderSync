# backend/routers/teste.py
from fastapi import APIRouter
from database import engine, SessionLocal
from models.teste import Teste, Base

router = APIRouter()

@router.post("/criar-teste")
def criar_tabela_e_inserir():
    # Cria a tabela se não existir
    Base.metadata.create_all(bind=engine)

    # Insere um registro
    db = SessionLocal()
    novo = Teste(nome="Dé Teste")
    db.add(novo)
    db.commit()
    db.close()

    return {"mensagem": "✅ Tabela criada e registro inserido com sucesso!"}
