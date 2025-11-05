from fastapi import APIRouter
from typing import Optional
from datetime import date
from pydantic import BaseModel

from database import SessionLocal

from schemas.produto import (
    ProdutoV2Create, ProdutoV2Update, ProdutoV2Out, ImpostoV2Create
)
from services.produto import (
    create_produto, update_produto, get_produto, list_produtos, get_anteriores
)

# deixa a tag mais limpa no Swagger
router = APIRouter(prefix="/api/produto", tags=["Produtos"])

class ProdutoCreatePayload(BaseModel):
    produto: ProdutoV2Create
    imposto: Optional[ImpostoV2Create] = None

@router.get(
    "",
    response_model=list[ProdutoV2Out],
    summary="Listar produtos",
    description="Busca produtos com filtros opcionais (q, status, família, vigência) e paginação.",
    operation_id="produtos_listar",
)
def listar_produtos(
    q: Optional[str] = None,
    status: Optional[str] = None,
    familia: Optional[int] = None,
    vigencia_em: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
):
    db = SessionLocal()
    try:
        return list_produtos(
            db,
            q=q,
            status=status,
            familia=familia,
            vigencia_em=vigencia_em,
            limit=limit,
            offset=offset,
        )
    finally:
        db.close()

@router.post(
    "",
    response_model=ProdutoV2Out,
    status_code=201,
    summary="Criar produto",
    description="Cria um novo produto (e imposto, se informado) e retorna o registro consolidado.",
    operation_id="produtos_criar",
)
def criar_produto(payload: ProdutoCreatePayload):
    db = SessionLocal()
    try:
        return create_produto(db, payload.produto, payload.imposto)
    finally:
        db.close()

@router.get(
    "/{produto_id}",
    response_model=ProdutoV2Out,
    summary="Obter produto por ID",
    description="Retorna os dados consolidados do produto a partir do ID.",
    operation_id="produtos_obter_por_id",
)
def obter_produto(produto_id: int):
    db = SessionLocal()
    try:
        return get_produto(db, produto_id)
    finally:
        db.close()

@router.patch(
    "/{produto_id}",
    response_model=ProdutoV2Out,
    summary="Atualizar produto (parcial)",
    description="Atualiza campos informados do produto (e imposto, se enviado) e retorna o consolidado.",
    operation_id="produtos_atualizar_parcial",
)
def atualizar_produto(
    produto_id: int,
    produto: ProdutoV2Update,
    imposto: Optional[ImpostoV2Create] = None
):
    db = SessionLocal()
    try:
        return update_produto(db, produto_id, produto, imposto)
    finally:
        db.close()

@router.get(
    "/{produto_id}/anteriores",
    summary="Consultar histórico (anteriores)",
    description="Retorna campos históricos/snapshots do produto (ex.: preço e unidade anteriores).",
    operation_id="produtos_consultar_anteriores",
)
def consultar_anteriores(produto_id: int):
    db = SessionLocal()
    try:
        return get_anteriores(db, produto_id)
    finally:
        db.close()
