from fastapi import APIRouter, Depends
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
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # 1. Faturamento do Mês e Ticket Médio
    # Usando status que NÃO sejam CANCELADO
    query_faturamento = text("""
        SELECT 
            COALESCE(SUM(total_pedido), 0) as faturado,
            COUNT(id_pedido) as qtd_pedidos
        FROM public.tb_pedidos
        WHERE status IN ('FATURADO', 'ENTREGUE')
          AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
          AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
    """)
    res_fat = db.execute(query_faturamento).mappings().first()
    faturamento = float(res_fat["faturado"] or 0.0)
    qtd_pedidos_faturados = int(res_fat["qtd_pedidos"] or 0)
    
    ticket_medio = 0.0
    if qtd_pedidos_faturados > 0:
        ticket_medio = faturamento / qtd_pedidos_faturados

    # 2. Pedidos Pendentes
    # Usando status = ABERTO ou qualquer outro que signifique pendente para o cliente
    query_pendentes = text("""
        SELECT COUNT(*) as qtd
        FROM public.tb_pedidos
        WHERE status NOT IN ('FATURADO', 'CANCELADO', 'DEVOLVIDO', 'ENTREGUE')
    """)
    res_pen = db.execute(query_pendentes).mappings().first()
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
