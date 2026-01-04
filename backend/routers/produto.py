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
from fastapi import Depends
from core.deps import get_current_user, get_db
from models.usuario import UsuarioModel


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
    db: Session = Depends(get_db)
):
    pdf_bytes = gerar_pdf_relatorio_lista(db, fornecedor, lista)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="relatorio_{fornecedor}_{lista}.pdf"'
        },
    )


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
def criar_produto_endpoint(payload: ProdutoCreatePayload, current_user: UsuarioModel = Depends(get_current_user)):
    db = SessionLocal()
    try:
        user_email = current_user.email
        # Modificar o payload antes de passar pro service
        payload.produto.criado_por = user_email
        payload.produto.atualizado_por = user_email
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
    current_user: UsuarioModel = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        produto.atualizado_por = current_user.email
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
    description="Importa PDF (INSUMOS/PET), grava na t_preco_produto_pdf_v2 e atualiza produtos.",
)
async def importar_lista(
    request: Request,
    tipo_lista: str = Form(..., description="Tipo de lista: INSUMOS ou PET"),
    validade_tabela: Optional[str] = Form(None),
    file: UploadFile = File(...),
    # Note: Using Depends in Form/File upload might be tricky if not done right, 
    # but Depends(get_current_user) works fine with OAuth2 header.
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):

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

    # Validar Data Manualmente para evitar 400 genérico do Pydantic/FastAPI
    dt_validade: Optional[date] = None
    if validade_tabela and validade_tabela.strip():
        try:
            # Tenta ISO primeiro
            dt_validade = date.fromisoformat(validade_tabela.strip())
        except ValueError:
            # Se falhar, tenta ignorar ou lançar erro específico
            # Vamos lançar erro específico para ajudar o usuário
            try:
                # Tenta parse básico caso venha formato estranho que não ISO (o front manda ISO, mas vai saber)
                from datetime import datetime
                dt_validade = datetime.strptime(validade_tabela.strip(), "%Y-%m-%d").date()
            except:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Data de validade inválida: {validade_tabela}. Use o formato AAAA-MM-DD."
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

    
    df["validade_tabela"] = dt_validade

    
    resumo = importar_pdf_para_produto(
        db,
        df,
        nome_arquivo=file.filename,
        usuario=current_user.email,
    )

    sync = resumo.get("sync", {})

    return {
        "arquivo": file.filename,
        "tipo_lista": tipo,
        "validade_tabela": dt_validade,
        "total_linhas_pdf": int(len(df)),
        "total_linhas": resumo.get("total_linhas"),
        "lista": resumo.get("lista"),
        "fornecedor": resumo.get("fornecedor"),
        # detalhamento da sincronização
        "sync": sync,
    }

class RenovarValidadeReq(BaseModel):
    nova_validade: date

@router.post("/renovar_validade_global")
def renovar_validade_global(payload: RenovarValidadeReq, current_user: UsuarioModel = Depends(get_current_user)):
    with SessionLocal() as db:
        from sqlalchemy import text
        try:
            # Atualiza todos os produtos ativos com a nova data
            res = db.execute(text("""
                UPDATE t_cadastro_produto_v2
                SET validade_tabela = :val,
                    atualizado_por = :user,
                    atualizado_em = NOW()
                WHERE status_produto = 'ATIVO'
            """), {"val": payload.nova_validade, "user": current_user.email})
            
            db.commit()
            return {"ok": True, "linhas_afetadas": res.rowcount, "nova_validade": payload.nova_validade}
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Erro ao renovar validade: {e}")

