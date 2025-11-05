from fastapi import APIRouter
from typing import Optional
from datetime import date
from pydantic import BaseModel

from database import SessionLocal

# Ajuste estes imports conforme os nomes reais dos seus módulos:
from schemas.produto import (
    ProdutoV2Create, ProdutoV2Update, ProdutoV2Out, ImpostoV2Create
)
from services.produto import (
    create_produto, update_produto, get_produto, list_produtos, get_anteriores
)

router = APIRouter(prefix="/api/produto", tags=["Produtos v2"])

# --------- CREATE ---------
class ProdutoCreatePayload(BaseModel):
    produto: ProdutoV2Create
    imposto: Optional[ImpostoV2Create] = None

@router.post("", response_model=ProdutoV2Out, status_code=201)
def api_create(payload: ProdutoCreatePayload):
    db = SessionLocal()
    try:
        return create_produto(db, payload.produto, payload.imposto)
    finally:
        db.close()

# --------- UPDATE ---------
@router.patch("/{produto_id}", response_model=ProdutoV2Out)
def api_update(
    produto_id: int,
    produto: ProdutoV2Update,
    imposto: Optional[ImpostoV2Create] = None
):
    db = SessionLocal()
    try:
        return update_produto(db, produto_id, produto, imposto)
    finally:
        db.close()

# --------- LIST / SEARCH ---------
@router.get("", response_model=list[ProdutoV2Out])
def api_list(
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

# --------- GET BY ID ---------
@router.get("/{produto_id}", response_model=ProdutoV2Out)
def api_get(produto_id: int):
    db = SessionLocal()
    try:
        return get_produto(db, produto_id)
    finally:
        db.close()

# --------- BLOCO "ANTERIORES" (opcional) ---------
@router.get("/{produto_id}/anteriores")
def api_get_anteriores(produto_id: int):
    db = SessionLocal()
    try:
        return get_anteriores(db, produto_id)
    finally:
        db.close()
