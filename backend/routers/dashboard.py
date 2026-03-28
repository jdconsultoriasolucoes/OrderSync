from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.deps import get_current_user
from models.usuario import UsuarioModel
import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def get_dashboard_filters(status: Optional[str] = None, periodo: str = "mes"):
    """
    Retorna o fragmento SQL WHERE (sem o 'WHERE' ou 'AND' inicial)
    e os parâmetros para os filtros globais.
    """
    hoje = datetime.date.today()
    params: Dict[str, Any] = {}
    where_parts: List[str] = []

    # 1. Filtro de Status
    if status and status != "Todos":
        where_parts.append("status = :status")
        params["status"] = status
    
    # 2. Filtro de Período
    start_date = None
    if periodo == "ytd":
        start_date = datetime.date(hoje.year, 1, 1)
    elif periodo == "trimestre":
        quarter_month = ((hoje.month - 1) // 3) * 3 + 1
        start_date = datetime.date(hoje.year, quarter_month, 1)
    elif periodo == "semestre":
        semester_month = 1 if hoje.month <= 6 else 7
        start_date = datetime.date(hoje.year, semester_month, 1)
    else: # "mes"
        start_date = datetime.date(hoje.year, hoje.month, 1)
    
    where_parts.append("created_at >= :start_date")
    params["start_date"] = start_date
    
    return " AND ".join(where_parts), params

@router.get("/geral")
def get_dashboard_geral(
    status: str = Query(None),
    periodo: str = Query("mes"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    where_clause, params = get_dashboard_filters(status, periodo)
    hoje = datetime.date.today()

    # KPIs
    q_kpi = text(f"""
        SELECT 
            COUNT(id_pedido) as pedidos_mes,
            COALESCE(SUM(total_pedido), 0) as faturamento_mes,
            COALESCE(AVG(total_pedido), 0) as ticket_medio
        FROM public.tb_pedidos
        WHERE {where_clause}
    """)
    kpi_row = db.execute(q_kpi, params).mappings().first()

    # Cargas (Ajustando filtro de data para cargas também)
    # tb_cargas usa data_criacao em vez de created_at
    c_where = where_clause.replace("created_at", "data_criacao")
    # Cargas não tem 'status' do pedido diretamente, então removemos se estiver filtrando por status?
    # No, idealmente cargas abertas seriam filtradas apenas por período se o status for de pedido.
    # Mas se o user filtrar por 'Cancelado', cargas abertas faz sentido? 
    # Por enquanto, aplicamos apenas o filtro de período nas cargas.
    _, c_params = get_dashboard_filters(None, periodo)
    q_cargas = text(f"""
        SELECT COUNT(id) as cargas_abertas
        FROM public.tb_cargas
        WHERE data_criacao >= :start_date
          AND (is_historico = FALSE OR is_historico IS NULL)
    """)
    cargas_row = db.execute(q_cargas, c_params).mappings().first()

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
            "pedidos_mes": int(kpi_row["pedidos_mes"] or 0),
            "faturamento_mes": float(kpi_row["faturamento_mes"] or 0),
            "ticket_medio": float(kpi_row["ticket_medio"] or 0),
            "cargas_abertas": int(cargas_row["cargas_abertas"] or 0)
        },
        "chart": {
            "labels": labels,
            "faturamento": faturamentos,
            "qtd_pedidos": qtds
        }
    }


@router.get("/vendas")
def get_dashboard_vendas(
    status: str = Query(None),
    periodo: str = Query("mes"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    where_clause, params = get_dashboard_filters(status, periodo)

    # Ticket médio especificado no período/status
    q_ticket = text(f"SELECT COALESCE(AVG(total_pedido), 0) as tkt FROM public.tb_pedidos WHERE total_pedido > 0 AND {where_clause}")
    tkt_row = db.execute(q_ticket, params).mappings().first()
    
    # Vendedores ativos vêm do cliente (elaboracao_vendedor)
    q_vendedores = text("SELECT COUNT(DISTINCT elaboracao_vendedor) as vends FROM public.t_cadastro_cliente_v2 WHERE elaboracao_vendedor IS NOT NULL AND elaboracao_vendedor != ''")
    vend_row = db.execute(q_vendedores).mappings().first()

    # Vendas por Região (Top 5 municípios)
    q_regiao = text(f"""
        SELECT COALESCE(c.faturamento_municipio, c.entrega_municipio) as mun, SUM(p.total_pedido) as total
        FROM public.tb_pedidos p
        JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
        WHERE {where_clause.replace('status =', 'p.status =').replace('created_at >=', 'p.created_at >=')}
        GROUP BY COALESCE(c.faturamento_municipio, c.entrega_municipio)
        ORDER BY total DESC
        LIMIT 5
    """)
    regioes = db.execute(q_regiao, params).mappings().all()
    reg_labels = [r["mun"] or "N/I" for r in regioes]
    reg_data = [float(r["total"] or 0) for r in regioes]

    # Vendas por Status
    # Nota: Este gráfico ignora o filtro de status para mostrar a proporção geral
    where_period, period_params = get_dashboard_filters(None, periodo)
    q_status = text(f"SELECT status, COUNT(id_pedido) as qtd FROM public.tb_pedidos WHERE {where_period} GROUP BY status")
    status_rows = db.execute(q_status, period_params).mappings().all()
    st_labels = [s["status"] for s in status_rows]
    st_data = [int(s["qtd"]) for s in status_rows]

    # Evolução Ticket Médio (Mês a Mês - 6 messes)
    hoje = datetime.date.today()
    evo_labels = []
    evo_ticket = []
    for i in range(5, -1, -1):
        dt = hoje - relativedelta(months=i)
        q_evo = text("""
            SELECT COALESCE(AVG(total_pedido), 0) as tkt
            FROM public.tb_pedidos
            WHERE status != 'Cancelado' AND total_pedido > 0
              AND EXTRACT(MONTH FROM created_at) = :m AND EXTRACT(YEAR FROM created_at) = :a
        """)
        row = db.execute(q_evo, {"m": dt.month, "a": dt.year}).mappings().first()
        evo_labels.append(dt.strftime("%b/%y"))
        evo_ticket.append(float(row["tkt"]))

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
        },
        "chart_evolucao_ticket": {
            "labels": evo_labels,
            "data": evo_ticket
        }
    }


@router.get("/logistica")
def get_dashboard_logistica(
    status: str = Query(None),
    periodo: str = Query("mes"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    where_clause, params = get_dashboard_filters(status, periodo)
    # Filtro de cargas (apenas período)
    _, p_params = get_dashboard_filters(None, periodo)

    q_kpi = text(f"""
        SELECT COUNT(id) as cargas_env
        FROM public.tb_cargas
        WHERE data_criacao >= :start_date
          AND is_historico = TRUE
    """)
    kpi_env = db.execute(q_kpi, p_params).mappings().first()

    hoje = datetime.date.today()
    q_peso = text(f"""
        SELECT COALESCE(AVG(carga_peso), 0) as peso_med
        FROM (
            SELECT cp.id_carga, SUM(COALESCE(p.peso_total_kg, 0)) as carga_peso
            FROM public.tb_cargas_pedidos cp
            JOIN public.tb_pedidos p ON cp.numero_pedido = CAST(p.id_pedido AS VARCHAR)
            WHERE {where_clause.replace('status =', 'p.status =').replace('created_at >=', 'p.created_at >=')}
            GROUP BY cp.id_carga
        ) sub
    """)
    kpi_peso = db.execute(q_peso, params).mappings().first()

    # Frete Total
    q_frete = text(f"""
        SELECT COALESCE(SUM(frete_total), 0) as total_frete 
        FROM public.tb_pedidos 
        WHERE {where_clause}
    """)
    kpi_frete = db.execute(q_frete, params).mappings().first()

    # Modalidade (Entrega vs Retirada)
    q_modalidade = text(f"""
        SELECT 
            COUNT(CASE WHEN frete_total > 0 THEN 1 END) as entrega,
            COUNT(CASE WHEN frete_total <= 0 THEN 1 END) as retirada
        FROM public.tb_pedidos
        WHERE {where_clause}
    """)
    mod_row = db.execute(q_modalidade, params).mappings().first()

    # Eficiência Frota (Próprio vs Terceiro)
    q_frota = text("""
        SELECT COALESCE(t.tipo_veiculo, 'Não Informado') as tipo, COUNT(c.id) as qtd
        FROM public.tb_cargas c
        JOIN public.tb_transporte t ON c.id_transporte = t.id
        GROUP BY t.tipo_veiculo
    """)
    frota_rows = db.execute(q_frota).mappings().all()

    labels = []
    pesos = []
    for i in range(5, -1, -1):
        dt = hoje - relativedelta(months=i)
        q_chart = text("""
            SELECT COALESCE(SUM(p.peso_total_kg), 0) as p
            FROM public.tb_cargas_pedidos cp
            JOIN public.tb_pedidos p ON cp.numero_pedido = CAST(p.id_pedido AS VARCHAR)
            JOIN public.tb_cargas c ON cp.id_carga = c.id
            WHERE EXTRACT(MONTH FROM c.data_criacao) = :m AND EXTRACT(YEAR FROM c.data_criacao) = :a
        """)
        row = db.execute(q_chart, {"m": dt.month, "a": dt.year}).mappings().first()
        labels.append(dt.strftime("%b/%y"))
        pesos.append(float(row["p"]))

    return {
        "kpis": {
            "cargas_enviadas_mes": int(kpi_env["cargas_env"] if kpi_env else 0),
            "peso_medio_carga": float(kpi_peso["peso_med"] if kpi_peso else 0),
            "custo_frete_mes": float(kpi_frete["total_frete"] if kpi_frete else 0)
        },
        "chart_historico": {
            "labels": labels,
            "data": pesos
        },
        "chart_modalidade": {
            "labels": ["Entrega", "Retirada"],
            "data": [int(mod_row["entrega"] or 0), int(mod_row["retirada"] or 0)]
        },
        "chart_frota": {
            "labels": [r["tipo"] for r in frota_rows],
            "data": [int(r["qtd"]) for r in frota_rows]
        }
    }


@router.get("/pivot")
def get_dashboard_pivot(
    status: Optional[str] = Query(None),
    periodo: str = Query("mes"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    where_clause, params = get_dashboard_filters(status, periodo)
    # Retorna uma lista de dicionários para o PivotTable.js
    q = text(f"""
        SELECT 
            p.status as "Status",
            COALESCE(c.faturamento_municipio, c.entrega_municipio) as "Municipio",
            p.cliente as "Cliente",
            p.total_pedido as "Valor_Total",
            TO_CHAR(p.created_at, 'YYYY-MM-DD') as "Data"
        FROM public.tb_pedidos p
        LEFT JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
        WHERE {where_clause.replace('status =', 'p.status =').replace('created_at >=', 'p.created_at >=')}
        ORDER BY p.created_at DESC
        LIMIT 2000
    """)
    rows = db.execute(q, params).mappings().all()
    
    return [dict(r) for r in rows]


@router.get("/kpis")
def get_dashboard_kpis(
    month: int = Query(None),
    year: int = Query(None),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """
    Retorna os KPIs principais para o dashboard da home (index.html).
    Suporta filtros por mês e ano.
    """
    hoje = datetime.date.today()
    # Filtro de data
    where_clause = ""
    params = {}
    
    if year:
        where_clause += " AND EXTRACT(YEAR FROM created_at) = :year"
        params["year"] = year
    if month:
        where_clause += " AND EXTRACT(MONTH FROM created_at) = :month"
        params["month"] = month

    # 1. Faturamento Total
    q_faturamento = text(f"""
        SELECT COALESCE(SUM(total_pedido), 0) as total
        FROM public.tb_pedidos
        WHERE status != 'Cancelado' {where_clause}
    """)
    faturamento = db.execute(q_faturamento, params).scalar() or 0

    # 2. Pedidos Pendentes (Status 'Pedido')
    # Nota: Pendentes aqui costumam ser os que ainda não foram faturados nem cancelados.
    q_pendentes = text(f"""
        SELECT COUNT(id_pedido)
        FROM public.tb_pedidos
        WHERE status = 'Pedido' {where_clause}
    """)
    pendentes = db.execute(q_pendentes, params).scalar() or 0

    # 3. Ticket Médio
    q_ticket = text(f"""
        SELECT COALESCE(AVG(total_pedido), 0) as avg_val
        FROM public.tb_pedidos
        WHERE status != 'Cancelado' AND total_pedido > 0 {where_clause}
    """)
    ticket_medio = db.execute(q_ticket, params).scalar() or 0

    return {
        "faturamento_mes": float(faturamento),
        "pedidos_pendentes": int(pendentes),
        "ticket_medio": float(ticket_medio)
    }

@router.get("/produtos")
def get_dashboard_produtos(
    status: str = Query(None),
    periodo: str = Query("mes"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    where_clause, params = get_dashboard_filters(status, periodo)

    # Top 10 Produtos
    q_top_produtos = text(f"""
        SELECT i.nome, SUM(i.quantidade) as qtd, COALESCE(SUM(i.subtotal_com_f), 0) as fat
        FROM public.tb_pedidos_itens i
        JOIN public.tb_pedidos p ON i.id_pedido = p.id_pedido
        WHERE {where_clause.replace('status =', 'p.status =').replace('created_at >=', 'p.created_at >=')} 
          AND i.nome IS NOT NULL AND i.nome != ''
        GROUP BY i.nome
        ORDER BY fat DESC
        LIMIT 10
    """)
    top_prods_rows = db.execute(q_top_produtos, params).mappings().all()

    # Distribuição por Família
    q_familias = text(f"""
        SELECT COALESCE(pr.familia, 'Sem Família') as fam, COALESCE(SUM(i.subtotal_com_f), 0) as fat
        FROM public.tb_pedidos_itens i
        JOIN public.tb_pedidos p ON i.id_pedido = p.id_pedido
        LEFT JOIN public.t_cadastro_produto_v2 pr ON i.codigo = pr.codigo_supra
        WHERE {where_clause.replace('status =', 'p.status =').replace('created_at >=', 'p.created_at >=')}
          AND pr.familia IS NOT NULL AND pr.familia != ''
        GROUP BY pr.familia
        ORDER BY fat DESC
        LIMIT 10
    """)
    familias_rows = db.execute(q_familias, params).mappings().all()

    return {
        "top_produtos": {
            "labels": [r["nome"] for r in top_prods_rows],
            "faturamento": [float(r["fat"]) for r in top_prods_rows],
            "quantidade": [float(r["qtd"]) for r in top_prods_rows]
        },
        "familias": {
            "labels": [r["fam"] for r in familias_rows],
            "faturamento": [float(r["fat"]) for r in familias_rows]
        }
    }

@router.get("/clientes")
def get_dashboard_clientes(
    status: str = Query(None),
    periodo: str = Query("mes"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    where_clause, params = get_dashboard_filters(status, periodo)

    # Top 10 Clientes (Ranking de Receita)
    q_top_cli = text(f"""
        SELECT p.cliente, COALESCE(SUM(p.total_pedido), 0) as fat
        FROM public.tb_pedidos p
        WHERE {where_clause.replace('status =', 'p.status =').replace('created_at >=', 'p.created_at >=')}
          AND p.cliente IS NOT NULL AND p.cliente != ''
        GROUP BY p.cliente
        ORDER BY fat DESC
        LIMIT 10
    """)
    top_cli_rows = db.execute(q_top_cli, params).mappings().all()

    # Funil de Conversão (Orçamentos vs Pedidos/Faturados)
    # Nota: Este kpi ignora o status 'Cancelado' mas respeita o período
    where_period, period_params = get_dashboard_filters(None, periodo)
    q_funil = text(f"""
        SELECT 
            COUNT(CASE WHEN status = 'Orçamento' THEN 1 END) as orcamentos,
            COUNT(CASE WHEN status != 'Orçamento' AND status != 'Cancelado' THEN 1 END) as convertidos
        FROM public.tb_pedidos
        WHERE {where_period}
    """)
    funil_row = db.execute(q_funil, period_params).mappings().first()

    # Ticket médio geral no período/status
    q_ticket_geral = text(f"SELECT COALESCE(AVG(total_pedido), 0) as med FROM public.tb_pedidos WHERE total_pedido > 0 AND {where_clause}")
    tkt_row = db.execute(q_ticket_geral, params).mappings().first()

    # Evolução Mensal de Novos Orçamentos vs Confirmados (6 meses)
    hoje = datetime.date.today()
    evo_labels = []
    evo_orcamentos = []
    evo_confirmados = []
    for i in range(5, -1, -1):
        dt = hoje - relativedelta(months=i)
        q_evo = text("""
            SELECT 
                COUNT(CASE WHEN status = 'Orçamento' THEN 1 END) as orcs,
                COUNT(CASE WHEN status != 'Orçamento' AND status != 'Cancelado' THEN 1 END) as confs
            FROM public.tb_pedidos
            WHERE EXTRACT(MONTH FROM created_at) = :m AND EXTRACT(YEAR FROM created_at) = :a
        """)
        row = db.execute(q_evo, {"m": dt.month, "a": dt.year}).mappings().first()
        evo_labels.append(dt.strftime("%b/%y"))
        evo_orcamentos.append(int(row["orcs"] or 0))
        evo_confirmados.append(int(row["confs"] or 0))

    return {
        "top_clientes": {
            "labels": [r["cliente"] for r in top_cli_rows],
            "faturamento": [float(r["fat"]) for r in top_cli_rows]
        },
        "funil": {
            "orcamentos": int(funil_row["orcamentos"] or 0),
            "convertidos": int(funil_row["convertidos"] or 0)
        },
        "kpis": {
            "ticket_record": float(tkt_row["med"] if tkt_row else 0)
        },
        "chart_evolucao_clientes": {
            "labels": evo_labels,
            "orcamentos": evo_orcamentos,
            "confirmados": evo_confirmados
        }
    }
