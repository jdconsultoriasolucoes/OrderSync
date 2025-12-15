from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query
from typing import Optional
from datetime import date
from pydantic import BaseModel
from fastapi.responses import Response

from database import SessionLocal
from sqlalchemy.orm import Session

from services.produto_pdf_data import parse_lista_precos
from services.produto_relatorio import gerar_pdf_relatorio_lista
from schemas.produto import (
    ProdutoV2Create,
    ProdutoV2Update,
    ProdutoV2Out,
    ImpostoV2Create,
)
from services.produto_pdf import (
    create_produto,
    update_produto,
    get_produto,
    list_produtos,
    get_anteriores,
    importar_pdf_para_produto,
)


# deixa a tag mais limpa no Swagger
router = APIRouter(prefix="/api/produto", tags=["Produtos"])


class ProdutoCreatePayload(BaseModel):
    produto: ProdutoV2Create
    imposto: Optional[ImpostoV2Create] = None


@router.get("/relatorio-lista", response_class=Response)
async def relatorio_lista(
    request: Request,
    fornecedor: str = Query(...),
    lista: str = Query(...),
):
    db: Session = request.state.db
    pdf_bytes = gerar_pdf_relatorio_lista(db, fornecedor, lista)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="relatorio_{fornecedor}_{lista}.pdf"'
        },
    )


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
def criar_produto_endpoint(payload: ProdutoCreatePayload):
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
def obter_produto_endpoint(produto_id: int):
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
def atualizar_produto_endpoint(
    produto_id: int,
    produto: ProdutoV2Update,
    imposto: Optional[ImpostoV2Create] = None,
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


@router.get(
    "/opcoes",
    summary="Obter opções de filtros",
    description="Retorna listas de valores distintos para preencher selects (Status, Giro, Família, etc).",
)
def obter_opcoes_endpoint():
    db = SessionLocal()
    try:
        from services.produto_pdf import get_product_options
        return get_product_options(db)
    finally:
        db.close()


@router.post(
    "/importar-lista",
    summary="Importar lista de preços via PDF",
    description="Importa PDF (INSUMOS/PET), grava na t_preco_produto_pdf_v2 e atualiza produtos.",
)
async def importar_lista(
    request: Request,
    tipo_lista: str = Form(..., description="Tipo de lista: INSUMOS ou PET"),
    validade_tabela: Optional[date] = Form(None),
    file: UploadFile = File(...),
):
    # pega a sessão criada pelo middleware (database.SessionLocal)
    db: Session = request.state.db

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="O arquivo precisa ser um PDF.")

    tipo_raw = tipo_lista.upper().strip()

    if tipo_raw in ("INS", "INSUMO", "INSUMOS"):
        tipo = "INSUMOS"
    elif tipo_raw in ("PET", "PETS", "PET"):
        tipo = "PET"
    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de lista inválido. Use INSUMOS ou PET.",
        )

    try:
        df = parse_lista_precos(file.file, tipo_lista=tipo, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler PDF: {e}")

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma linha válida encontrada no PDF.",
        )

    
    df["validade_tabela"] = validade_tabela

    
    resumo = importar_pdf_para_produto(
        db,
        df,
        nome_arquivo=file.filename,
        usuario="IMPORT_MANUAL",  # depois trocar pelo usuário logado
    )

    sync = resumo.get("sync", {})

    return {
        "arquivo": file.filename,
        "tipo_lista": tipo,
        "validade_tabela": validade_tabela,
        "total_linhas_pdf": int(len(df)),
        "total_linhas": resumo.get("total_linhas"),
        "lista": resumo.get("lista"),
        "fornecedor": resumo.get("fornecedor"),
        # detalhamento da sincronização
        "sync": sync,
    }

