from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from datetime import date
from pydantic import BaseModel

from database import SessionLocal

from schemas.produto import (
    ProdutoV2Create, ProdutoV2Update, ProdutoV2Out, ImpostoV2Create
)
from services.produto import (
    create_produto, update_produto, get_produto, list_produtos, get_anteriores,
    importar_lista_df,  # <-- nova função do service
)

from utils.pdf_lista_precos import parse_lista_precos  # ajusta o caminho se seu pacote for outro
import tempfile, shutil, os


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

@router.post(
    "/importar-lista",
    summary="Importar lista de preços via PDF",
    description="Recebe um PDF da lista de preços, extrai os itens e faz upsert na base de produtos.",
)
async def importar_lista(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")

    # checagem básica de tipo
    if file.content_type not in (
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF.")

    # salva PDF em arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    db = SessionLocal()
    try:
        # usa SUA função pra virar DataFrame
        df = parse_lista_precos(tmp_path)

        if df.empty:
            return {"total_linhas": 0, "inseridos": 0, "atualizados": 0}

        # chama a função do service pra gravar no banco
        resumo = importar_lista_df(db, df)
        return resumo

    finally:
        db.close()
        try:
            os.remove(tmp_path)
        except OSError:
            pass

