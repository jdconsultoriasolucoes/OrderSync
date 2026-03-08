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
    # 1. Fetch Carga info (Removed transport info for this report as requested)
    sql_carga = text("SELECT * FROM tb_cargas WHERE id = :cid")
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    # 2. Fetch Orders linked to this load
    sql_pedidos = text("""
        SELECT 
            cp.ordem_carregamento,
            p.id_pedido,
            p.status,
            p.cliente,
            p.fornecedor,
            CASE WHEN p.usar_valor_com_frete THEN 'C/ FRETE' ELSE 'S/ FRETE' END as modalidade,
            c.entrega_municipio as cidade,
            c.entrega_estado as uf,
            (SELECT SUM(quantidade) FROM tb_pedidos_itens WHERE id_pedido = p.id_pedido) as total_itens,
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

    # Table Data
    data = [["Ordem", "Pedido", "Status", "Cliente", "Fornecedor", "Frete", "Cidade/UF", "Itens", "Peso (kg)", "Valor Total"]]
    for p in pedidos:
        data.append([
            str(p.ordem_carregamento or ""),
            str(p.id_pedido),
            str(p.status or ""),
            str(p.cliente or "")[:25],
            str(p.fornecedor or "")[:15],
            str(p.modalidade),
            f"{p.cidade or ''}/{p.uf or ''}",
            str(int(p.total_itens or 0)),
            _br_number(p.peso_total_kg, 2),
            _br_number(p.valor_total, 2)
        ])

    # Table Style
    table = Table(data, colWidths=[1.2*cm, 1.8*cm, 2.0*cm, 5.0*cm, 3.0*cm, 2.0*cm, 4.0*cm, 1.5*cm, 2.2*cm, 2.8*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (7, 0), (-1, -1), 'RIGHT'), # Numbers to right
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
            c.entrega_municipio as cidade,
            c.entrega_bairro as bairro,
            p.peso_total_kg,
            p.total_pedido as valor_total
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

    subtitle = f"Carga: {carga.get('numero_carga') or ''} | Motorista: {carga.get('motorista') or ''} | Placa: {carga.get('veiculo_placa') or ''}"
    y = _draw_header(c, width, height, "Romaneio de Entrega", subtitle)

    # Transport Info Block
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.7*cm, y + 0.1*cm, "DADOS DO TRANSPORTE")
    c.setFont("Helvetica", 9)
    y -= 0.5*cm
    c.drawString(0.7*cm, y, f"Transportadora: {carga.get('transportadora') or 'Próprio'}")
    c.drawString(8.0*cm, y, f"Motorista: {carga.get('motorista') or '-'}")
    c.drawString(15.0*cm, y, f"Placa: {carga.get('veiculo_placa') or '-'}")
    y -= 0.8*cm

    data = [["Ord", "Pedido", "Cliente", "Cidade", "Bairro", "Peso (kg)", "Valor Total"]]
    for p in pedidos:
        data.append([
            str(p.ordem_carregamento or ""),
            str(p.id_pedido),
            str(p.cliente or "")[:45],
            str(p.cidade or "")[:25],
            str(p.bairro or "")[:25],
            _br_number(p.peso_total_kg, 2),
            _br_number(p.valor_total, 2)
        ])

    table = Table(data, colWidths=[1.0*cm, 2.0*cm, 10.0*cm, 4.5*cm, 4.5*cm, 2.5*cm, 3.0*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (5, 0), (-1, -1), 'RIGHT'),
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
            i.embalagem as item_embalagem
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos_itens i ON i.id_pedido::text = cp.numero_pedido::text
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, i.nome, i.embalagem
        ORDER BY i.nome
    """)
    produtos = db.execute(sql_resumo, {"cid": carga_id}).mappings().all()

    carga = db.execute(text("SELECT * FROM tb_cargas WHERE id = :cid"), {"cid": carga_id}).mappings().first()

    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    subtitle = f"Carga: {carga.get('numero_carga') or ''} - {carga.get('nome_carga') or ''}"
    y = _draw_header(c, width, height, "Resumo de Produtos por Carga", subtitle)

    data = [["Código", "Descrição", "Emb.", "Qtd Total"]]
    for p in produtos:
        data.append([
            str(p.item_codigo),
            str(p.item_nome)[:70],
            str(p.item_embalagem or ""),
            _br_number(p.qtd_total, 0)
        ])

    table = Table(data, colWidths=[3.0*cm, 10.0*cm, 2.0*cm, 3.0*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
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
# REPORT 4 - RELATÓRIO COMPLETO (MERGED)
# ----------------------------------------------------------------------------

def gerar_pdf_relatorio_completo(db, carga_id: int) -> bytes:
    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    _desenhar_romaneio_logic(c, db, carga_id, width, height)
    c.showPage()
    _desenhar_resumo_logic(c, db, carga_id, width, height)

    c.save()
    buffer.seek(0)
    return buffer.read()

def _desenhar_romaneio_logic(c, db, carga_id, width, height):
    sql_carga = text("""
        SELECT c.*, t.motorista, t.veiculo_placa, t.transportadora 
        FROM tb_cargas c 
        LEFT JOIN tb_transporte t ON c.id_transporte = t.id
        WHERE c.id = :cid
    """)
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return

    sql_pedidos = text("""
        SELECT 
            cp.ordem_carregamento,
            p.id_pedido,
            p.cliente,
            c.entrega_municipio as cidade,
            c.entrega_bairro as bairro,
            p.peso_total_kg,
            p.total_pedido as valor_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :cid
        ORDER BY cp.ordem_carregamento
    """)
    pedidos = db.execute(sql_pedidos, {"cid": carga_id}).mappings().all()

    subtitle = f"Carga: {carga.get('numero_carga') or ''} | Motorista: {carga.get('motorista') or ''} | Placa: {carga.get('veiculo_placa') or ''}"
    y = _draw_header(c, width, height, "Relatório Completo - Romaneio", subtitle)

    y -= 0.5*cm
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(0.7*cm, y, f"Transportadora: {carga.get('transportadora') or 'Próprio'}")
    c.drawString(8.0*cm, y, f"Motorista: {carga.get('motorista') or '-'}")
    c.drawString(15.0*cm, y, f"Placa: {carga.get('veiculo_placa') or '-'}")
    y -= 0.8*cm

    data = [["Ord", "Pedido", "Cliente", "Cidade", "Bairro", "Peso (kg)", "Valor Total"]]
    for p in pedidos:
        data.append([
            str(p.ordem_carregamento or ""),
            str(p.id_pedido),
            str(p.cliente or "")[:50],
            str(p.cidade or "")[:30],
            str(p.bairro or "")[:30],
            _br_number(p.peso_total_kg, 2),
            _br_number(p.valor_total, 2)
        ])

    table = Table(data, colWidths=[1.0*cm, 2.0*cm, 10.0*cm, 5.0*cm, 5.0*cm, 2.5*cm, 3.0*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (4, -1), 'LEFT'),
        ('ALIGN', (5, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0: style.add('BACKGROUND', (0, i), (-1, i), SUPRA_BG_LIGHT)
    
    table.setStyle(style)
    tw, th = table.wrap(width - 1.4*cm, height)
    table.drawOn(c, 0.7*cm, y - th)

def _desenhar_resumo_logic(c, db, carga_id, width, height):
    sql_resumo = text("""
        SELECT 
            i.codigo as item_codigo,
            i.nome as item_nome,
            SUM(i.quantidade) as qtd_total,
            i.embalagem as item_embalagem
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos_itens i ON i.id_pedido::text = cp.numero_pedido::text
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, i.nome, i.embalagem
        ORDER BY i.nome
    """)
    produtos = db.execute(sql_resumo, {"cid": carga_id}).mappings().all()

    carga = db.execute(text("SELECT * FROM tb_cargas WHERE id = :cid"), {"cid": carga_id}).mappings().first()

    subtitle = f"Carga: {carga.get('numero_carga') or ''} - {carga.get('nome_carga') or ''}"
    y = _draw_header(c, width, height, "Relatório Completo - Resumo de Produtos", subtitle)

    data = [["Código", "Descrição", "Emb.", "Qtd Total"]]
    for p in produtos:
        data.append([
            str(p.item_codigo),
            str(p.item_nome)[:75],
            str(p.item_embalagem or ""),
            _br_number(p.qtd_total, 0)
        ])

    table = Table(data, colWidths=[3.0*cm, 12.0*cm, 2.5*cm, 3.5*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0: style.add('BACKGROUND', (0, i), (-1, i), SUPRA_BG_LIGHT)
    
    table.setStyle(style)
    tw, th = table.wrap(width - 1.4*cm, height)
    table.drawOn(c, 0.7*cm, y - th)
