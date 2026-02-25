from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from pydantic import BaseModel
from core.deps import get_current_user
from models.usuario import UsuarioModel

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DashboardKPIs(BaseModel):
    faturamento_mes: float
    pedidos_pendentes: int
    contas_pagar: float
    contas_receber: float
    ticket_medio: float

@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(
    month: int = Query(None, description="Mês de referência (1-12)"),
    year: int = Query(None, description="Ano de referência (ex: 2024)"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    import datetime
    hoje = datetime.date.today()
    
    # Se ambos vierem vazios, assumimos o mês/ano atuais
    if not month and not year:
        month = hoje.month
        year = hoje.year
    # Se vier só o mês sem ano, assumimos ano atual
    elif month and not year:
        year = hoje.year

    # 1. Faturamento e Ticket Médio
    query_base_fat = """
        SELECT 
            COALESCE(SUM(total_pedido), 0) as faturado,
            COUNT(id_pedido) as qtd_pedidos
        FROM public.tb_pedidos
        WHERE status IN ('FATURADO', 'ENTREGUE')
    """
    
    params = {}
    if year:
        query_base_fat += " AND EXTRACT(YEAR FROM created_at) = :year "
        params["year"] = year
    if month:
        query_base_fat += " AND EXTRACT(MONTH FROM created_at) = :month "
        params["month"] = month
        
    res_fat = db.execute(text(query_base_fat), params).mappings().first()
    faturamento = float(res_fat["faturado"] or 0.0)
    qtd_pedidos_faturados = int(res_fat["qtd_pedidos"] or 0)
    
    ticket_medio = 0.0
    if qtd_pedidos_faturados > 0:
        ticket_medio = faturamento / qtd_pedidos_faturados

    # 2. Pedidos Pendentes
    query_base_pen = """
        SELECT COUNT(*) as qtd
        FROM public.tb_pedidos
        WHERE status NOT IN ('FATURADO', 'CANCELADO', 'DEVOLVIDO', 'ENTREGUE')
    """
    
    if year:
        query_base_pen += " AND EXTRACT(YEAR FROM created_at) = :year "
    if month:
        query_base_pen += " AND EXTRACT(MONTH FROM created_at) = :month "
        
    res_pen = db.execute(text(query_base_pen), params).mappings().first()
    pedidos_pendentes = int(res_pen["qtd"] or 0)

    # 3. Contas a Pagar e Receber (Módulo Financeiro ainda não integrado, mock temporário ou 0)
    contas_pagar = 0.0
    contas_receber = 0.0

    return DashboardKPIs(
        faturamento_mes=faturamento,
        pedidos_pendentes=pedidos_pendentes,
        contas_pagar=contas_pagar,
        contas_receber=contas_receber,
        ticket_medio=ticket_medio
    )
