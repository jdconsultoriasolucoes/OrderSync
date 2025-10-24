# backend/routers/pedidos.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import SessionLocal  # usa seu database.py
from services.pedidos import (
    LISTAGEM_SQL, COUNT_SQL, RESUMO_SQL, ITENS_JSON_SQL,
    STATUS_SQL, STATUS_UPDATE_SQL, STATUS_EVENT_INSERT_SQL
)

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class PedidoListItem(BaseModel):
    numero_pedido: int
    data_pedido: datetime
    cliente_nome: str
    cliente_codigo: Optional[str] = None
    modalidade: str
    valor_total: float
    status_codigo: str
    tabela_preco_nome: Optional[str] = None
    fornecedor: Optional[str] = None
    link_url: Optional[str] = None
    link_status: Optional[str] = None
    link_enviado: bool

class ListagemResponse(BaseModel):
    data: List[PedidoListItem]
    page: int
    pageSize: int
    total: int

class PedidoItemResumo(BaseModel):
    codigo: str
    nome: Optional[str] = None
    embalagem: Optional[str] = None
    quantidade: float
    preco_unit: float
    subtotal: float

class PedidoResumo(BaseModel):
    id_pedido: int
    codigo_cliente: Optional[str] = None
    cliente: str
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    contato_fone: Optional[str] = None
    tabela_preco_nome: Optional[str] = None
    fornecedor: Optional[str] = None
    validade_ate: Optional[str] = None
    validade_dias: Optional[int] = None
    usar_valor_com_frete: bool
    peso_total_kg: float
    frete_total: float
    total_pedido: float
    observacoes: Optional[str] = None
    status: str
    confirmado_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None
    cancelado_motivo: Optional[str] = None
    link_url: Optional[str] = None
    link_primeiro_acesso_em: Optional[datetime] = None
    link_status: Optional[str] = None
    created_at: datetime
    itens: List[PedidoItemResumo] = Field(default_factory=list)

class StatusEntry(BaseModel):
    codigo: str
    rotulo: str
    cor_hex: Optional[str] = None
    ordem: Optional[int] = None
    ativo: Optional[bool] = True

class StatusListResponse(BaseModel):
    data: List[StatusEntry]

class StatusChangeBody(BaseModel):
    para: str
    motivo: Optional[str] = None
    user_id: Optional[str] = None

# ---------- Routes ----------
@router.get("", response_model=ListagemResponse)
def listar_pedidos(
    from_: Optional[str] = Query(None, alias="from"),  # string "YYYY-MM-DD"
    to_:   Optional[str] = Query(None, alias="to"),    # string "YYYY-MM-DD"
    status: Optional[str] = Query(None),
    tabela_nome: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    fornecedor: Optional[str] = Query(None),
    page: int = 1,
    pageSize: int = 25,
    db: Session = Depends(get_db),
):
    # 1. fallback de período padrão (últimos 30 dias)
    if not from_ or not to_:
        hoje = datetime.now()
        inicio = hoje - timedelta(days=30)
        from_ = inicio.strftime("%Y-%m-%d")
        to_   = hoje.strftime("%Y-%m-%d")

    # 2. normaliza as datas p/ intervalo fechado do dia
    try:
        from_dt = datetime.strptime(from_, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # OBS: no SQL você está usando >= :from AND < :to
        # então aqui o to_dt tem que ser dia seguinte meia-noite
        # (porque usamos "< :to", não "<= :to")
        limite_to = datetime.strptime(to_, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
    except ValueError:
        return {"data": [], "page": page, "pageSize": pageSize, "total": 0}

    # 3. paginação
    limit = pageSize
    offset = (page - 1) * pageSize
    if offset < 0:
        offset = 0

    # 4. trata filtros opcionais
    # status pode vir "ABERTO,CONFIRMADO"
    status_list = status.split(",") if status else None

    params_base = {
        "from": from_dt,
        "to": limite_to,
        "status_list": status_list,
        "tabela_nome": f"%{tabela_nome}%" if tabela_nome else None,
        "cliente_busca": f"%{cliente}%" if cliente else None,
        "fornecedor_busca": f"%{fornecedor}%" if fornecedor else None,
    }

    # 5. total
    total_row = db.execute(COUNT_SQL, params_base).mappings().first()
    total = total_row["total"] if total_row and "total" in total_row else 0

    # 6. dados paginados
    params_listagem = {
        **params_base,
        "limit": limit,
        "offset": offset,
    }
    rows_raw = db.execute(LISTAGEM_SQL, params_listagem).mappings().all()

    # 7. montar objetos da resposta no formato do schema PedidoListItem
    rows = []
    for r in rows_raw:
        rows.append(PedidoListItem(
            numero_pedido      = r["numero_pedido"],
            data_pedido        = r["data_pedido"],
            cliente_nome       = r["cliente_nome"],
            cliente_codigo     = r["cliente_codigo"],
            modalidade         = r["modalidade"],
            valor_total        = r["valor_total"],
            status_codigo      = r["status_codigo"],
            tabela_preco_nome  = r["tabela_preco_nome"],
            fornecedor         = r["fornecedor"],
            link_url           = r["link_url"],
            link_status        = r["link_status"],
            link_enviado       = r["link_enviado"],
        ))

    return {
        "data": rows,
        "page": page,
        "pageSize": pageSize,
        "total": total,
    }

@router.get("/{id_pedido}/resumo", response_model=PedidoResumo)
def resumo_pedido(id_pedido: int, db: Session = Depends(get_db)):
    head = db.execute(RESUMO_SQL, {"id_pedido": id_pedido}).mappings().first()
    if not head:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    itens_json = db.execute(ITENS_JSON_SQL, {"id_pedido": id_pedido}).mappings().first()
    itens = itens_json["itens"] if itens_json and itens_json["itens"] else []
    head_dict = dict(head)
    head_dict["itens"] = [PedidoItemResumo(**i) for i in itens]
    return PedidoResumo(**head_dict)

@router.get("/status", response_model=StatusListResponse)
def listar_status(db: Session = Depends(get_db)):
    rows = db.execute(STATUS_SQL).mappings().all()
    data = [StatusEntry(**dict(r)) for r in rows]
    return StatusListResponse(data=data)

@router.post("/{id_pedido}/status")
def mudar_status(id_pedido: int, body: StatusChangeBody, db: Session = Depends(get_db)):
    cur = db.execute(text("SELECT status FROM public.tb_pedidos WHERE id_pedido=:id"), {"id": id_pedido}).first()
    if not cur:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    de_status = cur[0]

    upd = db.execute(STATUS_UPDATE_SQL, {"para_status": body.para, "id_pedido": id_pedido}).first()
    if upd is None:
        raise HTTPException(status_code=400, detail="Falha ao atualizar status")

    # log (silencioso no MVP se tabela não existir)
    try:
        db.execute(STATUS_EVENT_INSERT_SQL, {
            "pedido_id": id_pedido,
            "de_status": de_status,
            "para_status": body.para,
            "user_id": body.user_id,
            "motivo": body.motivo,
            "metadata": "{}"
        })
    except Exception:
        pass

    db.commit()
    return {"ok": True}
