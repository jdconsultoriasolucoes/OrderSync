from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query, BackgroundTasks
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
    delete_produto,
)
from fastapi import Depends
from core.deps import get_current_user, get_db
from models.usuario import UsuarioModel
from models.background_task import BackgroundTaskModel
from services.worker_recalculo import processar_recalculo_massivo
import uuid

def trigger_recalculo(task_id: str, codigos_alterados: list):
    with SessionLocal() as db_bg:
        task = db_bg.query(BackgroundTaskModel).filter_by(task_id=task_id).first()
        if task:
            processar_recalculo_massivo(db_bg, task, codigos_alterados)


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
    status: Optional[str] = "ATIVO",
    familia: Optional[int] = None,
    fornecedor: Optional[str] = None,
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
            fornecedor=fornecedor,
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


@router.get("/ultimo_estoque_nome")
def obter_ultimo_estoque_nome():
    db = SessionLocal()
    try:
        from models.produto import HistoricoEstoqueV2
        latest_hist = db.query(HistoricoEstoqueV2.nome_arquivo)\
            .filter(HistoricoEstoqueV2.nome_arquivo != None)\
            .order_by(HistoricoEstoqueV2.data_ingestao.desc())\
            .first()
        if latest_hist:
            return {"nome_arquivo": latest_hist[0]}
        
        # Fallback de busca nos produtos
        from models.produto import ProdutoV2
        prod = db.query(ProdutoV2.nome_arquivo_estoque)\
            .filter(ProdutoV2.nome_arquivo_estoque != None)\
            .first()
        if prod:
            return {"nome_arquivo": prod[0]}
            
        return {"nome_arquivo": None}
    except Exception as e:
        return {"nome_arquivo": None}
    finally:
        db.close()


class EstoqueLoteRequest(BaseModel):
    codigos: list[str]

@router.post("/estoque-lote")
def obter_estoque_lote(payload: EstoqueLoteRequest, db: Session = Depends(get_db)):
    """Busca o estoque atualizado (disponivel e futuro) de uma lista de códigos."""
    from models.produto import ProdutoV2
    
    # Limpa e formata os códigos enviados
    codigos = [c.strip() for c in payload.codigos if c and c.strip()]
    if not codigos:
        return {}

    # Busca status e estoque diretamente de ProdutoV2
    rows_produto = db.query(
        ProdutoV2.codigo_supra,
        ProdutoV2.status_produto,
        ProdutoV2.estoque_disponivel,
        ProdutoV2.estoque_futuro,
        ProdutoV2.nome_arquivo_estoque,
    ).filter(
        ProdutoV2.codigo_supra.in_(codigos)
    ).all()

    stock_map = {}
    status_map = {}
    
    # Monta mapa com fallback correto para duplos
    for r in rows_produto:
        rs = (r.status_produto or "").upper()
        cod_db = str(r.codigo_supra).strip()
        
        if cod_db not in status_map or (status_map[cod_db] != 'ATIVO' and rs == 'ATIVO'):
            status_map[cod_db] = rs
            stock_map[cod_db] = {
                "estoque_disponivel": int(r.estoque_disponivel or 0),
                "estoque_futuro": int(r.estoque_futuro or 0),
                "nome_arquivo": r.nome_arquivo_estoque,
                "status": rs
            }
            
    return stock_map



@router.get("/diag_estoque")
def diagnostico_estoque():
    """Endpoint temporário de diagnóstico do estado do estoque no banco."""
    from models.produto import HistoricoEstoqueV2
    with SessionLocal() as db:
        try:
            total = db.execute(text("SELECT COUNT(*) FROM t_historico_estoque_v2")).scalar()
            total_ativos = db.execute(text("SELECT COUNT(*) FROM t_historico_estoque_v2 WHERE ativo = TRUE")).scalar()
            total_inativos = db.execute(text("SELECT COUNT(*) FROM t_historico_estoque_v2 WHERE ativo = FALSE OR ativo IS NULL")).scalar()
            ultimos = db.execute(text(
                "SELECT codigo_supra, estoque_disponivel, estoque_futuro, ativo, nome_arquivo, data_ingestao "
                "FROM t_historico_estoque_v2 ORDER BY data_ingestao DESC LIMIT 10"
            )).mappings().all()
            return {
                "total_registros": total,
                "total_ativos": total_ativos,
                "total_inativos": total_inativos,
                "ultimos_10": [dict(r) for r in ultimos]
            }
        except Exception as e:
            return {"erro": str(e)}


@router.get("/relatorio-estoque")
def gerar_relatorio_estoque(
    divisao: str = Query("", description="Filtro de Divisão (INSUMOS, PET)"),
    giro: str = Query("", description="Filtro de Tipo de Giro (A, B, C)"),
    familia: str = Query("", description="Filtro de Família"),
    produto: str = Query("", description="Filtro de Produto (Nome ou Código)"),
    db: Session = Depends(get_db)
):
    from models.produto import ProdutoV2
    from sqlalchemy import or_
    
    query = db.query(
        ProdutoV2.codigo_supra,
        ProdutoV2.nome_produto,
        ProdutoV2.peso_bruto,
        ProdutoV2.estoque_disponivel,
        ProdutoV2.estoque_futuro,
        ProdutoV2.estoque_ideal,
        ProdutoV2.tipo,
        ProdutoV2.tipo_giro,
        ProdutoV2.preco,
        ProdutoV2.preco_anterior
    ).filter(ProdutoV2.status_produto == 'ATIVO')

    if divisao:
        query = query.filter(ProdutoV2.tipo == divisao)
    
    if giro:
        query = query.filter(ProdutoV2.tipo_giro == giro)
        
    if familia:
        query = query.filter(ProdutoV2.familia == familia)
        
    if produto:
        termo = f"%{produto}%"
        query = query.filter(
            or_(
                ProdutoV2.nome_produto.ilike(termo),
                ProdutoV2.codigo_supra.ilike(termo)
            )
        )

    # Ordenar por descrição para facilitar
    produtos = query.order_by(ProdutoV2.nome_produto.asc()).all()

    resultado = []
    for p in produtos:
        resultado.append({
            "codigo_supra": p.codigo_supra,
            "nome_produto": p.nome_produto,
            "peso_bruto": float(p.peso_bruto) if p.peso_bruto else 0.0,
            "estoque_disponivel": int(p.estoque_disponivel or 0),
            "estoque_futuro": int(p.estoque_futuro or 0),
            "estoque_ideal": int(p.estoque_ideal or 0),
            "divisao": p.tipo,
            "tipo_giro": p.tipo_giro,
            "preco": float(p.preco) if p.preco else 0.0,
            "preco_anterior": float(p.preco_anterior) if p.preco_anterior else 0.0
        })

    return resultado


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

@router.delete(
    "/{produto_id}",
    status_code=204,
    summary="Excluir produto",
    description="Remove um produto pelo ID. Retorna 204 No Content.",
    operation_id="produtos_excluir",
)
def excluir_produto_endpoint(produto_id: int):
    db = SessionLocal()
    try:
        delete_produto(db, produto_id)
        return Response(status_code=204)
    finally:
        db.close()






@router.post(
    "/importar-lista",
    summary="Importar lista de preços via PDF",
    description="Importa PDF (INSUMOS/PET), grava na t_preco_produto_pdf_v2 e atualiza produtos.",
)
async def importar_lista(
    request: Request,
    background_tasks: BackgroundTasks,
    tipo_lista: str = Form(..., description="Tipo de lista: INSUMOS ou PET"),
    fornecedor: Optional[str] = Form(None, description="Nome do fornecedor (opcional, sobrescreve detecção)"),
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
        df = parse_lista_precos(file.file, tipo_lista=tipo, filename=file.filename, fornecedor_selecionado=fornecedor)
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

    codigos_alterados = []
    for g in sync.get("grupos", []):
        codigos_alterados.extend(g.get("codigos_alterados", []))
        
    task_id = None
    if codigos_alterados:
        task_id = str(uuid.uuid4())
        nova_tarefa = BackgroundTaskModel(
            task_id=task_id,
            tipo_tarefa="RECALCULO_MASSIVO",
            status="PENDENTE",
            mensagem_status="Aguardando início do recálculo...",
        )
        db.add(nova_tarefa)
        db.commit()
        
        background_tasks.add_task(trigger_recalculo, task_id, codigos_alterados)

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
        "task_id": task_id,
    }

@router.get("/task-status/{task_id}")
def obter_status_tarefa(task_id: str, db: Session = Depends(get_db)):
    task = db.query(BackgroundTaskModel).filter_by(task_id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progresso": task.progresso,
        "mensagem_status": task.mensagem_status,
        "tipo_tarefa": task.tipo_tarefa,
        "erro": task.erro
    }

class RenovarValidadeReq(BaseModel):
    nova_validade: date
    tipo: Optional[str] = "TODOS" # TODOS, INSUMOS, PET

@router.post("/renovar_validade_global")
def renovar_validade_global(payload: RenovarValidadeReq, current_user: UsuarioModel = Depends(get_current_user)):
    with SessionLocal() as db:
        from sqlalchemy import text
        try:
            # Filtro base
            where_clause = "UPPER(status_produto) = 'ATIVO'"
            params = {"val": payload.nova_validade, "user": current_user.email}

            # Filtro opcional por tipo
            if payload.tipo and payload.tipo.upper() != "TODOS":
                where_clause += " AND tipo = :tipo"
                params["tipo"] = payload.tipo.upper()

            # Atualiza todos os produtos ativos com a nova data (e filtro opcional)
            query = f"""
                UPDATE t_cadastro_produto_v2
                SET validade_tabela = :val,
                    atualizado_por = :user,
                    updated_at = NOW()
                WHERE {where_clause}
            """

            res = db.execute(text(query), params)
            
            db.commit()
            return {"ok": True, "linhas_afetadas": res.rowcount, "nova_validade": payload.nova_validade}
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Erro ao renovar validade: {e}")


@router.post(
    "/importar-estoque",
    summary="Importar planilha de estoque (.xlsx)",
    description="Carrega arquivo Excel de estoque, calcula estoque disponível e futuro, e atualiza produtos.",
)
async def importar_estoque(
    file: UploadFile = File(...),
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="O arquivo precisa ser uma planilha Excel (.xlsx).")

    try:
        import pandas as pd
        # Read Excel file using pandas
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo Excel: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="A planilha está vazia.")

    success_count = 0
    not_found_codes = []
    total_rows = 0

    from models.produto import ProdutoV2, HistoricoEstoqueV2

    # Desativa a flag de histórico ativo para todos os históricos de estoque anteriores
    try:
        db.query(HistoricoEstoqueV2).update({HistoricoEstoqueV2.ativo: False}, synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=f"Erro ao resetar histórico de estoque ativo no banco: {e}")

    for idx, row in df.iterrows():
        # Skip completely empty rows
        if row.isnull().all():
            continue

        # Look up product code: first column or by typical name candidates
        def get_val_by_name_or_idx(names: list[str], pos: int):
            for name in names:
                if name in row:
                    return row[name]
            if len(row) > pos:
                return row.iloc[pos]
            return None

        codigo_raw = get_val_by_name_or_idx(["Produto", "CODIGO", "CÓDIGO", "Codigo", "Código"], 0)
        if pd.isna(codigo_raw) or not str(codigo_raw).strip():
            continue

        codigo_str = str(codigo_raw).strip()
        total_rows += 1

        def safe_int(val):
            if pd.isna(val) or val is None:
                return 0
            try:
                return int(float(val))
            except:
                return 0

        # Columns F (5), G (6), H (7) positional and header fallback
        qtd_estoque = safe_int(get_val_by_name_or_idx(["Qt. Estoque", "Qt Estoque", "Qtd Estoque", "Qtd. Estoque"], 5))
        qtd_pedidos = safe_int(get_val_by_name_or_idx(["Qt. Pedidos Carteira", "Qt. Pedidos", "Qt Pedidos", "Qtd Pedidos"], 6))
        af_pendentes = safe_int(get_val_by_name_or_idx(["AF Pendentes", "AF Pendente", "AF"], 7))

        estoque_disponivel = qtd_estoque - qtd_pedidos
        estoque_futuro = estoque_disponivel + af_pendentes

        # Update in database using bulk query update
        updated = db.query(ProdutoV2).filter(ProdutoV2.codigo_supra == codigo_str).update({
            ProdutoV2.estoque_disponivel: estoque_disponivel,
            ProdutoV2.estoque_futuro: estoque_futuro,
            ProdutoV2.nome_arquivo_estoque: file.filename
        }, synchronize_session=False)


        if updated > 0:
            success_count += updated
        else:
            not_found_codes.append(codigo_str)

        # Salva registro no histórico de ingestão
        nome_prod = get_val_by_name_or_idx(["Descrição", "DESCRIÇÃO", "Descriçao", "Descricao", "Descrio"], 1)
        nome_prod_str = str(nome_prod).strip() if not pd.isna(nome_prod) else None

        from models.produto import HistoricoEstoqueV2
        hist_entry = HistoricoEstoqueV2(
            codigo_supra=codigo_str,
            nome_produto=nome_prod_str,
            qtd_estoque=qtd_estoque,
            qtd_pedido=qtd_pedidos,
            af_pendentes=af_pendentes,
            estoque_disponivel=estoque_disponivel,
            estoque_futuro=estoque_futuro,
            nome_arquivo=file.filename,
            usuario=current_user.email,
            ativo=True
        )
        db.add(hist_entry)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=f"Erro ao salvar atualizações de estoque no banco: {e}")

    return {
        "sucesso": True,
        "total_linhas": total_rows,
        "atualizados": success_count,
        "nao_encontrados": not_found_codes
    }


