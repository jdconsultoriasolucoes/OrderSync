from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from database import SessionLocal
from services.pedidos import (
    listar_pedidos_orm, get_pedido_resumo, listar_status_orm, update_status_orm
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
    cliente_nome: Optional[str] = None
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
    cliente: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    contato_fone: Optional[str] = None
    tabela_preco_nome: Optional[str] = None
    fornecedor: Optional[str] = None
    validade_ate: Optional[date] = None
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
    from_: Optional[str] = Query(None, alias="from"),
    to_:   Optional[str] = Query(None, alias="to"),
    status: Optional[str] = Query(None),
    tabela_nome: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    fornecedor: Optional[str] = Query(None),
    page: int = 1,
    pageSize: int = 25,
    db: Session = Depends(get_db),
):
    # 1. Date Handling
    if not from_ or not to_:
        hoje = datetime.now()
        inicio = hoje - timedelta(days=30)
        from_dt = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        limite_to = hoje.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        try:
            from_dt = datetime.strptime(from_, "%Y-%m-%d")
            limite_to = datetime.strptime(to_, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return {"data": [], "page": page, "pageSize": pageSize, "total": 0}

    # 2. Status List
    status_list = [s.strip() for s in status.split(",") if s.strip()] if status else None

    # 3. Filters
    filters = {
        "from": from_dt,
        "to": limite_to,
        "status_list": status_list,
        "tabela_nome": tabela_nome,
        "cliente": cliente,
        "fornecedor": fornecedor
    }

    # 4. Call Service
    rows, total = listar_pedidos_orm(db, page, pageSize, filters)

    return {
        "data": rows,
        "page": page,
        "pageSize": pageSize,
        "total": total,
    }

@router.get("/{id_pedido}/resumo", response_model=PedidoResumo)
def resumo_pedido(id_pedido: int, db: Session = Depends(get_db)):
    data = get_pedido_resumo(db, id_pedido)
    if not data:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    pedido = data["pedido"]
    items_models = data["itens"]
    nome_tabela = data["nome_tabela"]
    
    # Map items
    itens_resumo = []
    for it in items_models:
        # Calculate displayed price based on 'usar_valor_com_frete'
        if pedido.usar_valor_com_frete:
            p_unit = it.preco_unit_frt or 0
            sub = it.subtotal_com_f or 0
        else:
            p_unit = it.preco_unit or 0
            sub = it.subtotal_sem_f or 0
            
        itens_resumo.append(PedidoItemResumo(
            codigo=it.codigo,
            nome=it.nome,
            embalagem=it.embalagem,
            quantidade=it.quantidade,
            preco_unit=p_unit,
            subtotal=sub
        ))

    return PedidoResumo(
        id_pedido=pedido.id_pedido,
        codigo_cliente=pedido.codigo_cliente,
        cliente=pedido.cliente,
        contato_nome=pedido.contato_nome,
        contato_email=pedido.contato_email,
        contato_fone=pedido.contato_fone,
        tabela_preco_nome=nome_tabela,
        fornecedor=pedido.fornecedor,
        validade_ate=pedido.validade_ate,
        validade_dias=pedido.validade_dias,
        usar_valor_com_frete=pedido.usar_valor_com_frete,
        peso_total_kg=pedido.peso_total_kg,
        frete_total=pedido.frete_total,
        total_pedido=pedido.total_pedido,
        observacoes=pedido.observacoes,
        status=pedido.status,
        confirmado_em=pedido.confirmado_em,
        cancelado_em=pedido.cancelado_em,
        cancelado_motivo=pedido.cancelado_motivo,
        link_url=pedido.link_url,
        link_primeiro_acesso_em=pedido.link_primeiro_acesso_em,
        link_status=pedido.link_status,
        created_at=pedido.created_at,
        itens=itens_resumo
    )

@router.get("/status", response_model=StatusListResponse)
def listar_status(db: Session = Depends(get_db)):
    rows = listar_status_orm(db)
    # rows are dict-like mappings
    data = [StatusEntry(**dict(r)) for r in rows]
    return StatusListResponse(data=data)

@router.post("/{id_pedido}/status")
def mudar_status(id_pedido: int, body: StatusChangeBody, db: Session = Depends(get_db)):
    updated = update_status_orm(db, id_pedido, body.para, body.user_id, body.motivo)
    if not updated:
        raise HTTPException(status_code=404, detail="Pedido não encontrado ou falha ao atualizar")
    
    return {"ok": True}
