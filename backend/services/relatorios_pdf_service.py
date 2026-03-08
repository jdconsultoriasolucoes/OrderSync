# backend/services/relatorios_pdf_service.py

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from pathlib import Path
import io
from sqlalchemy import text

# Palette and standard formatters (based on pdf_service.py)
SUPRA_BAR = colors.Color(0.78, 0.70, 0.60)       # Header bar
SUPRA_TEXT = colors.Color(0.1, 0.1, 0.1)        # Dark text
SUPRA_BG_LIGHT = colors.Color(0.95, 0.95, 0.95) # Alternating rows

def _br_number(value, decimals=2, suffix=""):
    if value is None: value = 0
    try: value = float(value)
    except: value = 0.0
    fmt = f"{{:,.{decimals}f}}"
    s = fmt.format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s + suffix

def _get_logo_path():
    base_dir = Path(__file__).resolve().parents[2]
    # Try to find logo in known locations
    candidates = [
        base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png",
        base_dir / "frontend" / "public" / "logo_cliente_supra.png",
        base_dir / "frontend" / "public" / "logo.png"
    ]
    for p in candidates:
        if p.exists(): return p
    return None

def _draw_header(c, width, height, title, subtitle=""):
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm
    available_width = width - 2 * margin_x
    top_y = height - margin_y

    # Logo
    logo_path = _get_logo_path()
    logo_h = 0
    if logo_path:
        try:
            img = ImageReader(str(logo_path))
            logo_w = 3.0 * cm
            iw, ih = img.getSize()
            logo_h = logo_w * ih / iw
            c.drawImage(img, width - margin_x - logo_w, top_y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask="auto")
        except: pass

    # Header Bar
    faixa_h = 1.0 * cm
    faixa_y = top_y - logo_h - 0.2 * cm
    c.setFillColor(SUPRA_BAR)
    c.rect(margin_x, faixa_y - faixa_h, available_width, faixa_h, stroke=0, fill=1)

    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x + 0.3 * cm, faixa_y - faixa_h + 0.3 * cm, title.upper())

    # Subtitle / Date
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin_x, faixa_y - faixa_h + 0.55 * cm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if subtitle:
        c.drawRightString(width - margin_x, faixa_y - faixa_h + 0.15 * cm, subtitle)

    return faixa_y - faixa_h - 0.5 * cm

# ----------------------------------------------------------------------------
# REPORT 1 - MANUTENÇÃO DE PEDIDOS / FORMAÇÃO DE CARGAS
# ----------------------------------------------------------------------------

def gerar_pdf_formacao_carga(db, carga_id: int) -> bytes:
    # 1. Fetch Carga info
    sql_carga = text("SELECT * FROM tb_cargas WHERE id = :cid")
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    # 2. Fetch Orders linked to this load
    sql_pedidos = text("""
        SELECT 
            cp.ordem_carregamento,
            p.id_pedido,
            p.cliente,
            p.nome_fantasia,
            CASE WHEN p.usar_valor_com_frete THEN 'C/ FRETE' ELSE 'S/ FRETE' END as modalidade,
            c.entrega_municipio as cidade,
            c.entrega_rota_principal as rota_geral,
            c.entrega_rota_aproximacao as rota_aprox,
            p.peso_total_kg,
            p.total_pedido as valor_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :cid
        ORDER BY cp.ordem_carregamento
    """)
    pedidos = db.execute(sql_pedidos, {"cid": carga_id}).mappings().all()

    # 3. Draw PDF
    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    subtitle = f"Carga: {carga.get('numero_carga') or ''} - {carga.get('nome_carga') or ''}"
    y = _draw_header(c, width, height, "Manutenção de Pedidos / Formação de Carga", subtitle)

    # Extra Header - Campo p/ Digitar
    c.setFont("Helvetica", 10)
    c.drawString(width - 5.5*cm, height - 1.5*cm, "Campo p/ Digitar Nº Carga: ________________")

    # Table Data
    # Columns: Nº CARGA | Nº PEDIDO | PESO LIQUIDO | CÓDIGO | CLIENTE | N. FANTASIA | MUNICÍPIO | ROTA GERAL | ROTA DE APROXIMAÇÃO
    data = [["Nº CARGA", "Nº PEDIDO", "PESO LIQ.", "CÓDIGO", "CLIENTE", "N. FANTASIA", "MUNICÍPIO", "ROTA GERAL", "ROTA APROX."]]
    
    for p in pedidos:
        data.append([
            str(carga.get('numero_carga') or ""),
            str(p.id_pedido),
            _br_number(p.peso_total_kg, 2),
            str(p.id_pedido), # Using ID as code if no specific code
            str(p.cliente or "")[:20],
            str(p.nome_fantasia or "")[:15],
            str(p.cidade or "")[:15],
            str(p.rota_geral or "-"),
            str(p.rota_aprox or "-")
        ])

    # Table Style
    table = Table(data, colWidths=[1.8*cm, 1.8*cm, 2.0*cm, 1.8*cm, 5.0*cm, 3.5*cm, 3.5*cm, 4.0*cm, 4.5*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'), # Peso Liq
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0: style.add('BACKGROUND', (0, i), (-1, i), SUPRA_BG_LIGHT)
    
    table.setStyle(style)
    tw, th = table.wrap(width - 1.4*cm, height)
    table.drawOn(c, 0.7*cm, y - th)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

# ----------------------------------------------------------------------------
# REPORT 2 - ROMANEIO
# ----------------------------------------------------------------------------

def gerar_pdf_romaneio(db, carga_id: int) -> bytes:
    sql_carga = text("""
        SELECT c.*, t.motorista, t.veiculo_placa, t.transportadora 
        FROM tb_cargas c 
        LEFT JOIN tb_transporte t ON c.id_transporte = t.id
        WHERE c.id = :cid
    """)
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    sql_pedidos = text("""
        SELECT 
            cp.ordem_carregamento,
            p.id_pedido,
            p.cliente,
            p.nome_fantasia,
            c.entrega_municipio as cidade,
            p.peso_total_kg,
            cp.observacoes as obs_carga
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :cid
        ORDER BY cp.ordem_carregamento
    """)
    pedidos = db.execute(sql_pedidos, {"cid": carga_id}).mappings().all()

    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    # Header Info from drawing
    # Filial (static or from env as a placeholder for now), CARGA Nº, DATA
    y = _draw_header(c, width, height, "Romaneio de Entrega")

    # Header Block
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.7*cm, y, f"Filial: SUPRA LOG")
    c.drawString(8.0*cm, y, f"CARGA Nº: {carga.get('numero_carga') or ''}")
    c.drawRightString(width - 0.7*cm, y, f"DATA: {datetime.now().strftime('%d/%m/%Y')}")
    y -= 0.6*cm
    
    c.drawString(0.7*cm, y, f"TRANSPORTADORA: {carga.get('transportadora') or 'Próprio'}")
    c.drawString(8.0*cm, y, f"MOTORISTA: {carga.get('motorista') or '-'}")
    c.drawRightString(width - 0.7*cm, y, f"VEÍCULO/PLACA: {carga.get('veiculo_placa') or '-'}")
    y -= 1.0*cm

    # Table columns: CÓDIGO | CLIENTE | N. FANTASIA | MUNICÍPIO | ORDEM CARREG. | PESO LÍQUIDO | OBSERVAÇÃO PEDIDO
    data = [["CÓDIGO", "CLIENTE", "N. FANTASIA", "MUNICÍPIO", "ORDEM CARREG.", "PESO LÍQUIDO", "OBSERVAÇÃO PEDIDO"]]
    for p in pedidos:
        data.append([
            str(p.id_pedido),
            str(p.cliente or "")[:35],
            str(p.nome_fantasia or "")[:20],
            str(p.cidade or "")[:20],
            str(p.ordem_carregamento or ""),
            _br_number(p.peso_total_kg, 2),
            str(p.obs_carga or "")[:40]
        ])

    table = Table(data, colWidths=[2.0*cm, 7.0*cm, 4.0*cm, 4.0*cm, 2.5*cm, 2.5*cm, 5.0*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0: style.add('BACKGROUND', (0, i), (-1, i), SUPRA_BG_LIGHT)
    
    table.setStyle(style)
    tw, th = table.wrap(width - 1.4*cm, height)
    table.drawOn(c, 0.7*cm, y - th)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

# ----------------------------------------------------------------------------
# REPORT 3 - RESUMO DE PRODUTOS
# ----------------------------------------------------------------------------

def gerar_pdf_resumo_produtos(db, carga_id: int) -> bytes:
    sql_resumo = text("""
        SELECT 
            i.codigo as item_codigo,
            i.nome as item_nome,
            SUM(i.quantidade) as qtd_total,
            MAX(i.embalagem) as item_embalagem,
            CAST(SUM(i.quantidade * COALESCE(prod.peso, 0)) AS FLOAT) AS peso_liquido_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        JOIN tb_pedidos_itens i ON i.id_pedido = p.id_pedido
        LEFT JOIN (
            SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso
            FROM t_cadastro_produto_v2
            GROUP BY codigo_supra
        ) prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, i.nome
        ORDER BY peso_liquido_total DESC
    """)
    produtos = db.execute(sql_resumo, {"cid": carga_id}).mappings().all()
    carga = db.execute(text("SELECT * FROM tb_cargas WHERE id = :cid"), {"cid": carga_id}).mappings().first()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Internal draw logic to reuse in Completo
    _desenhar_resumo_logic(c, db, carga, produtos, width, height)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def _desenhar_resumo_logic(c, db, carga, produtos, width, height, y_start=None):
    if y_start is None:
        y = _draw_header(c, width, height, "Resumo de Produtos por Carga")
        # Header Info: Filial, CARGA Nº, DATA
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.7*cm, y, f"Filial: SUPRA LOG")
        c.drawString(7.0*cm, y, f"CARGA Nº: {carga.get('numero_carga') or ''}")
        c.drawRightString(width - 0.7*cm, y, f"DATA: {datetime.now().strftime('%d/%m/%Y')}")
        y -= 1.0*cm
    else:
        y = y_start

    # Table columns: CÓDIGO | DESCRIÇÃO PRODUTO / EMBALAGEM | PESO LÍQUIDO | EMBALAGEM | PESO LÍQUIDO ACUMULADO
    data = [["CÓDIGO", "DESCRIÇÃO PRODUTO / EMBALAGEM", "PESO LÍQUIDO", "EMBALAGEM", "PESO LÍQ. ACUM."]]
    
    acumulado = 0.0
    for p in produtos:
        peso = p.peso_liquido_total or 0.0
        acumulado += peso
        data.append([
            str(p.item_codigo),
            str(p.item_nome)[:55],
            _br_number(peso, 3),
            str(p.item_embalagem or ""),
            _br_number(acumulado, 3)
        ])

    table = Table(data, colWidths=[2.5*cm, 8.5*cm, 2.5*cm, 2.5*cm, 3.5*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0: style.add('BACKGROUND', (0, i), (-1, i), SUPRA_BG_LIGHT)
    
    table.setStyle(style)
    tw, th = table.wrap(width - 1.4*cm, height)
    table.drawOn(c, 0.7*cm, y - th)
    return y - th

# ----------------------------------------------------------------------------
# REPORT 4 - RELATÓRIO COMPLETO (MERGED)
# ----------------------------------------------------------------------------

def gerar_pdf_relatorio_completo(db, carga_id: int) -> bytes:
    # Fetch all info for both parts
    sql_carga = text("""
        SELECT c.*, t.motorista, t.veiculo_placa, t.transportadora 
        FROM tb_cargas c 
        LEFT JOIN tb_transporte t ON c.id_transporte = t.id
        WHERE c.id = :cid
    """)
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    sql_pedidos = text("""
        SELECT 
            cp.ordem_carregamento,
            p.id_pedido,
            p.cliente,
            p.nome_fantasia,
            c.entrega_municipio as cidade,
            p.peso_total_kg,
            cp.observacoes as obs_carga
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :cid
        ORDER BY cp.ordem_carregamento
    """)
    pedidos = db.execute(sql_pedidos, {"cid": carga_id}).mappings().all()

    sql_resumo = text("""
        SELECT 
            i.codigo as item_codigo,
            i.nome as item_nome,
            SUM(i.quantidade) as qtd_total,
            MAX(i.embalagem) as item_embalagem,
            CAST(SUM(i.quantidade * COALESCE(prod.peso, 0)) AS FLOAT) AS peso_liquido_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        JOIN tb_pedidos_itens i ON p.id_pedido = i.id_pedido
        LEFT JOIN (
            SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso
            FROM t_cadastro_produto_v2
            GROUP BY codigo_supra
        ) prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, i.nome
        ORDER BY peso_liquido_total DESC
    """)
    produtos = db.execute(sql_resumo, {"cid": carga_id}).mappings().all()

    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    # Part 1: Romaneio
    y = _desenhar_romaneio_logic(c, carga, pedidos, width, height)

    # Add space and Part 2: Resumo
    y -= 1.0 * cm
    # If not enough room, new page
    if y < 4 * cm:
        c.showPage()
        y = None # None triggers draw_header

    c.setFont("Helvetica-Bold", 11)
    if y is None: y = _draw_header(c, width, height, "Relatório Completo - Resumo de Produtos")
    else: c.drawString(0.7*cm, y + 0.2*cm, "RESUMO DE PRODUTOS")

    _desenhar_resumo_logic(c, db, carga, produtos, width, height, y_start=y)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def _desenhar_romaneio_logic(c, carga, pedidos, width, height):
    y = _draw_header(c, width, height, "Romaneio de Entrega")

    # Header Info: Filial, CARGA Nº, DATA
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.7*cm, y, f"Filial: SUPRA LOG")
    c.drawString(8.0*cm, y, f"CARGA Nº: {carga.get('numero_carga') or ''}")
    c.drawRightString(width - 0.7*cm, y, f"DATA: {datetime.now().strftime('%d/%m/%Y')}")
    y -= 0.6*cm
    
    c.drawString(0.7*cm, y, f"TRANSPORTADORA: {carga.get('transportadora') or 'Próprio'}")
    c.drawString(8.0*cm, y, f"MOTORISTA: {carga.get('motorista') or '-'}")
    c.drawRightString(width - 0.7*cm, y, f"VEÍCULO/PLACA: {carga.get('veiculo_placa') or '-'}")
    y -= 1.0*cm

    # Table columns: CÓDIGO | CLIENTE | N. FANTASIA | MUNICÍPIO | ORDEM CARREG. | PESO LÍQUIDO | OBSERVAÇÃO PEDIDO
    data = [["CÓDIGO", "CLIENTE", "N. FANTASIA", "MUNICÍPIO", "ORDEM CARREG.", "PESO LÍQUIDO", "OBSERVAÇÃO PEDIDO"]]
    for p in pedidos:
        data.append([
            str(p.id_pedido),
            str(p.cliente or "")[:35],
            str(p.nome_fantasia or "")[:20],
            str(p.cidade or "")[:20],
            str(p.ordem_carregamento or ""),
            _br_number(p.peso_total_kg, 2),
            str(p.obs_carga or "")[:40]
        ])

    table = Table(data, colWidths=[2.0*cm, 7.0*cm, 4.0*cm, 4.0*cm, 2.5*cm, 2.5*cm, 5.0*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0: style.add('BACKGROUND', (0, i), (-1, i), SUPRA_BG_LIGHT)
    
    table.setStyle(style)
    tw, th = table.wrap(width - 1.4*cm, height)
    table.drawOn(c, 0.7*cm, y - th)
    return y - th
