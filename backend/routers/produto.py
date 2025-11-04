# routers/produtos_v2.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from db.session import get_db  # ajuste para o seu get_db real
from schemas.produto_v2 import (
    ProdutoV2Create, ProdutoV2Update, ProdutoV2Out, ImpostoV2Create
)
from services.produtos_v2_service import (
    create_produto, update_produto, get_produto, list_produtos, get_anteriores
)

router = APIRouter(prefix="/api/produtos-v2", tags=["Produtos v2"])

# --------- CREATE ---------
class ProdutoCreatePayload(BaseModel):
    produto: ProdutoV2Create
    imposto: Optional[ImpostoV2Create] = None

from pydantic import BaseModel

@router.post("", response_model=ProdutoV2Out, status_code=201)
def api_create(payload: ProdutoCreatePayload, db: Session = Depends(get_db)):
    return create_produto(db, payload.produto, payload.imposto)

# --------- UPDATE ---------
@router.patch("/{produto_id}", response_model=ProdutoV2Out)
def api_update(produto_id: int, produto: ProdutoV2Update, imposto: Optional[ImpostoV2Create] = None, db: Session = Depends(get_db)):
    return update_produto(db, produto_id, produto, imposto)

# --------- LIST / SEARCH ---------
@router.get("", response_model=list[ProdutoV2Out])
def api_list(
    q: Optional[str] = None,
    status: Optional[str] = None,
    familia: Optional[int] = None,
    vigencia_em: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return list_produtos(db, q=q, status=status, familia=familia, vigencia_em=vigencia_em, limit=limit, offset=offset)

# --------- GET BY ID ---------
@router.get("/{produto_id}", response_model=ProdutoV2Out)
def api_get(produto_id: int, db: Session = Depends(get_db)):
    return get_produto(db, produto_id)

# --------- BLOCO "ANTERIORES" (opcional) ---------
@router.get("/{produto_id}/anteriores")
def api_get_anteriores(produto_id: int, db: Session = Depends(get_db)):
    return get_anteriores(db, produto_id)
