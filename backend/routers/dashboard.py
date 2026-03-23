from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from pydantic import BaseModel
from typing import List, Dict, Any
from core.deps import get_current_user
from models.usuario import UsuarioModel
import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/geral")
def get_dashboard_geral(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    hoje = datetime.date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # KPIs
    q_kpi = text("""
        SELECT 
            COUNT(id_pedido) as pedidos_mes,
            COALESCE(SUM(total_pedido), 0) as faturamento_mes
        FROM public.tb_pedidos
        WHERE EXTRACT(MONTH FROM created_at) = :mes AND EXTRACT(YEAR FROM created_at) = :ano
    """)
    kpi_row = db.execute(q_kpi, {"mes": mes_atual, "ano": ano_atual}).mappings().first()

    q_cargas = text("""
        SELECT COUNT(id) as cargas_abertas
        FROM public.m_carga
        WHERE status_carga != 'FINALIZADA' AND status_carga != 'CANCELADA'
    """)
    cargas_row = db.execute(q_cargas).mappings().first()

    # Gráfico (últimos 6 meses)
    labels = []
    faturamentos = []
    qtds = []
    
    for i in range(5, -1, -1):
        dt = hoje - relativedelta(months=i)
        q_chart = text("""
            SELECT 
                COUNT(id_pedido) as qtd,
                COALESCE(SUM(total_pedido), 0) as fat
            FROM public.tb_pedidos
            WHERE EXTRACT(MONTH FROM created_at) = :m AND EXTRACT(YEAR FROM created_at) = :a
        """)
        row = db.execute(q_chart, {"m": dt.month, "a": dt.year}).mappings().first()
        labels.append(dt.strftime("%b/%y"))
        faturamentos.append(float(row["fat"]))
        qtds.append(int(row["qtd"]))

    return {
        "kpis": {
            "pedidos_mes": int(kpi_row["pedidos_mes"] if kpi_row and kpi_row["pedidos_mes"] else 0),
            "faturamento_mes": float(kpi_row["faturamento_mes"] if kpi_row and kpi_row["faturamento_mes"] else 0),
            "cargas_abertas": int(cargas_row["cargas_abertas"] if cargas_row and cargas_row["cargas_abertas"] else 0)
        },
        "chart": {
            "labels": labels,
            "faturamento": faturamentos,
            "qtd_pedidos": qtds
        }
    }


@router.get("/vendas")
def get_dashboard_vendas(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Ticket médio geral
    q_ticket = text("SELECT COALESCE(AVG(total_pedido), 0) as tkt FROM public.tb_pedidos WHERE total_pedido > 0")
    tkt_row = db.execute(q_ticket).mappings().first()
    
    # Vendedores ativos vêm do cliente (elaboracao_vendedor)
    q_vendedores = text("SELECT COUNT(DISTINCT elaboracao_vendedor) as vends FROM public.t_cadastro_cliente_v2 WHERE elaboracao_vendedor IS NOT NULL AND elaboracao_vendedor != ''")
    vend_row = db.execute(q_vendedores).mappings().first()

    # Vendas por Região (Top 5 municípios)
    q_regiao = text("""
        SELECT c.cadastro_municipio as mun, SUM(p.total_pedido) as total
        FROM public.tb_pedidos p
        JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
        GROUP BY c.cadastro_municipio
        ORDER BY total DESC
        LIMIT 5
    """)
    regioes = db.execute(q_regiao).mappings().all()
    reg_labels = [r["mun"] or "N/I" for r in regioes]
    reg_data = [float(r["total"] or 0) for r in regioes]

    # Vendas por Status
    q_status = text("SELECT status, COUNT(id_pedido) as qtd FROM public.tb_pedidos GROUP BY status")
    status_rows = db.execute(q_status).mappings().all()
    st_labels = [s["status"] for s in status_rows]
    st_data = [int(s["qtd"]) for s in status_rows]

    return {
        "kpis": {
            "ticket_medio": float(tkt_row["tkt"] if tkt_row else 0),
            "vendedores_ativos": int(vend_row["vends"] if vend_row else 0)
        },
        "chart_regioes": {
            "labels": reg_labels,
            "data": reg_data
        },
        "chart_status": {
            "labels": st_labels,
            "data": st_data
        }
    }


@router.get("/logistica")
def get_dashboard_logistica(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    hoje = datetime.date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    q_kpi = text("""
        SELECT COUNT(id) as cargas_env
        FROM public.m_carga
        WHERE EXTRACT(MONTH FROM created_at) = :m AND EXTRACT(YEAR FROM created_at) = :a
    """)
    kpi_env = db.execute(q_kpi, {"m": mes_atual, "a": ano_atual}).mappings().first()

    q_peso = text("""
        SELECT COALESCE(AVG(peso_bruto_total), 0) as peso_med
        FROM public.m_carga
        WHERE peso_bruto_total > 0
    """)
    kpi_peso = db.execute(q_peso).mappings().first()

    # Histórico de peso das cargas nas ultimas semanas/meses (vamos usar os ultimos 6 meses)
    labels = []
    pesos = []
    for i in range(5, -1, -1):
        dt = hoje - relativedelta(months=i)
        q_chart = text("""
            SELECT COALESCE(SUM(peso_bruto_total), 0) as p
            FROM public.m_carga
            WHERE EXTRACT(MONTH FROM created_at) = :m AND EXTRACT(YEAR FROM created_at) = :a
        """)
        row = db.execute(q_chart, {"m": dt.month, "a": dt.year}).mappings().first()
        labels.append(dt.strftime("%b/%y"))
        pesos.append(float(row["p"]))

    return {
        "kpis": {
            "cargas_enviadas_mes": int(kpi_env["cargas_env"] if kpi_env else 0),
            "peso_medio_carga": float(kpi_peso["peso_med"] if kpi_peso else 0)
        },
        "chart_historico": {
            "labels": labels,
            "data": pesos
        }
    }


@router.get("/pivot")
def get_dashboard_pivot(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Retorna uma lista de dicionários para o PivotTable.js
    q = text("""
        SELECT 
            p.status as "Status",
            c.cadastro_municipio as "Municipio",
            p.cliente_nome as "Cliente",
            p.total_pedido as "Valor_Total",
            TO_CHAR(p.created_at, 'YYYY-MM') as "Mes_Ano"
        FROM public.tb_pedidos p
        LEFT JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
        ORDER BY p.created_at DESC
        LIMIT 1000
    """)
    rows = db.execute(q).mappings().all()
    
    return [dict(r) for r in rows]
