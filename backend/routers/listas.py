from fastapi import APIRouter
from data.listas import SITUAÇÃO, RETIRA, TIPO_PESSOA, TIPOS_CLIENTE, SUPERVISOR, ATIVIDADE_PRINCIPAL, ROTA, tipo_venda, tipo_compra, ramo_de_atividade

router = APIRouter()

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
def get_rota():
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