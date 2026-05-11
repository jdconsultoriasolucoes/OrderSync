from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from data.listas import SITUAÇÃO, RETIRA, TIPO_PESSOA, TIPOS_CLIENTE, SUPERVISOR, ATIVIDADE_PRINCIPAL, ROTA, TIPO_VENDA, TIPO_COMPRA, RAMO_DE_ATIVIDADE

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/situacao")
def get_situacao():
    return SITUAÇÃO

@router.get("/retira")
def get_retira():
    return RETIRA

@router.get("/tipo_pessoa")
def get_tipo_pessoa():
    return TIPO_PESSOA

@router.get("/tipos_cliente")
def get_tipos_cliente():
    return TIPOS_CLIENTE

@router.get("/supervisor")
def get_supervisor():
    return SUPERVISOR

@router.get("/atividade_principal")
def get_atividade_principal():
    return ATIVIDADE_PRINCIPAL

@router.get("/rota")
def get_rota(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        # Busca a lista concatenada da tabela de referência
        rows = db.execute(text("SELECT rota, municipio FROM tb_municipio_rota ORDER BY rota")).mappings().all()
        if not rows:
            # Fallback para lista fixa se o banco estiver vazio
            return ROTA
        return [f"{r['rota']} - {r['municipio']}" for r in rows]
    except Exception:
        # Fallback de segurança para não quebrar o frontend
        return ROTA

@router.get("/tipo_venda")
def get_tipo_venda():
    return TIPO_VENDA

@router.get("/tipo_compra")
def get_tipo_compra():
    return TIPO_COMPRA

@router.get("/ramo_de_atividade")
def get_ramo_de_atividade():
    return RAMO_DE_ATIVIDADE