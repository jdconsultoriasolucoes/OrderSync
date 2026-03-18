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
from copy import copy
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
    sql_pedidos = text("""SELECT
            cp.ordem_carregamento,
            p.id_pedido,
            p.codigo_cliente,
            COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente,
            c.cadastro_nome_fantasia as nome_fantasia,
            CASE WHEN p.usar_valor_com_frete THEN 'C/ FRETE' ELSE 'S/ FRETE' END as modalidade,
            c.entrega_municipio as cidade,
            c.entrega_rota_principal as rota_geral,
            c.entrega_rota_aproximacao as rota_aprox,
            p.peso_total_kg,
            COALESCE(pb.peso_bruto_total, p.peso_total_kg) as peso_bruto_total,
            p.total_pedido as valor_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN (
             SELECT 
                 id_pedido,
                 SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) as peso_bruto_total
             FROM tb_pedidos_itens i
             LEFT JOIN (
                 SELECT codigo_supra, MAX(peso) as peso, MAX(peso_bruto) as peso_bruto 
                 FROM t_cadastro_produto_v2 GROUP BY codigo_supra
             ) prod ON prod.codigo_supra = i.codigo
             GROUP BY id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :cid
        ORDER BY cp.ordem_carregamento""")
    pedidos = db.execute(sql_pedidos, {"cid": carga_id}).mappings().all()

    # 3. Draw PDF
    total_liq = sum(p.peso_total_kg or 0 for p in pedidos)
    total_bruto = sum(p.peso_bruto_total or 0 for p in pedidos)

    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    subtitle = f"Carga: {carga.get('numero_carga') or ''} - {carga.get('nome_carga') or ''}"
    y = _draw_header(c, width, height, "Manutenção de Pedidos / Formação de Carga", subtitle)

    # Totais no cabeçalho — canto direito, acima da tabela
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawRightString(width - 0.7*cm, y, f"TOTAL P. LÍQ: {_br_number(total_liq, 0)} kg   |   TOTAL P. BRUTO: {_br_number(total_bruto, 0)} kg")
    y -= 0.8*cm

    # Table Data
    # Columns: Nº CARGA | Nº PEDIDO | PESO LÍQ. ACUM | CÓDIGO | CLIENTE | N. FANTASIA | MUNICÍPIO | ROTA G. | ROTA A.
    styles = getSampleStyleSheet()
    style_wrapped = copy(styles["Normal"])
    style_wrapped.fontSize = 7
    style_wrapped.leading = 8
    style_wrapped.textColor = colors.black

    # style_header for wrapping
    style_header = copy(styles["Normal"])
    style_header.fontSize = 8
    style_header.leading = 9
    style_header.fontName = 'Helvetica-Bold'
    style_header.textColor = colors.white
    style_header.alignment = 0 # Left

    header_labels = ["Nº CARGA", "Nº PEDIDO", "PESO LÍQ. ACUM", "CÓDIGO", "CLIENTE", "N. FANTASIA", "MUNICÍPIO", "ROTA G.", "ROTA A."]
    header_row = [Paragraph(h, style_header) for h in header_labels]

    data = [header_row]

    for p in pedidos:
        cliente_p = Paragraph(str(p.cliente or ""), style_wrapped)
        fantasia_p = Paragraph(str(p.nome_fantasia or ""), style_wrapped)
        cidade_p = Paragraph(str(p.cidade or ""), style_wrapped)

        data.append([
            str(carga.get('numero_carga') or ""),
            str(p.id_pedido),
            _br_number(p.peso_total_kg, 0),
            str(p.codigo_cliente or p.id_pedido),
            cliente_p,
            fantasia_p,
            cidade_p,
            str(p.rota_geral or "")[:2],
            str(p.rota_aprox or "")[:2]
        ])

    # 9 colunas: sem Peso Br. Acum
    col_widths = [1.4*cm, 1.6*cm, 2.2*cm, 1.6*cm, 8.0*cm, 5.0*cm, 4.3*cm, 1.6*cm, 1.6*cm]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Peso Líq.
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
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
        SELECT c.*, t.motorista, t.modelo, t.veiculo_placa, t.transportadora 
        FROM tb_cargas c 
        LEFT JOIN tb_transporte t ON c.id_transporte = t.id
        WHERE c.id = :cid
    """)
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    sql_pedidos = text("""SELECT 
            cp.ordem_carregamento,
            p.id_pedido,
            p.codigo_cliente,
            COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente,
            c.cadastro_nome_fantasia as nome_fantasia,
            c.entrega_municipio as cidade,
            p.peso_total_kg,
            COALESCE(pb.peso_bruto_total, p.peso_total_kg) as peso_bruto_total,
            cp.observacoes as obs_carga
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN (
             SELECT 
                 id_pedido,
                 SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) as peso_bruto_total
             FROM tb_pedidos_itens i
             LEFT JOIN (
                 SELECT codigo_supra, MAX(peso) as peso, MAX(peso_bruto) as peso_bruto 
                 FROM t_cadastro_produto_v2 GROUP BY codigo_supra
             ) prod ON prod.codigo_supra = i.codigo
             GROUP BY id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
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
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.7*cm, y, f"Filial: SUPRA LOG")
    c.drawString(8.0*cm, y, f"CARGA Nº: {carga.get('numero_carga') or ''}")
    # User requested Data do carregamento in header too
    data_carregamento = carga.get('data_carregamento')
    data_str = data_carregamento.strftime('%d/%m/%Y') if data_carregamento else '____/____/____'
    c.drawRightString(width - 0.7*cm, y, f"DATA CARREGAMENTO: {data_str}")
    y -= 0.5*cm

    # Totais: calculados aqui para exibir abaixo do veículo
    total_liq_val = sum(p.peso_total_kg or 0 for p in pedidos)
    total_bruto_val = sum(p.peso_bruto_total or 0 for p in pedidos)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.7*cm, y, f"TRANSPORTADORA: {carga.get('transportadora') or 'Próprio'}")
    c.drawString(8.0*cm, y, f"MOTORISTA: {carga.get('motorista') or '-'}")
    c.drawRightString(width - 0.7*cm, y, f"VEÍCULO: {carga.get('modelo') or '-'} / PLACA: {carga.get('veiculo_placa') or '-'}")
    y -= 0.8*cm
    # Totais abaixo da linha do veículo, canto direito
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - 0.7*cm, y, f"TOTAL P. LÍQ: {_br_number(total_liq_val, 0)} kg   |   TOTAL P. BRUTO: {_br_number(total_bruto_val, 0)} kg")
    y -= 0.3*cm

    # Table columns: CÓDIGO | CLIENTE | N. FANTASIA | MUNICÍPIO | ORDEM | PESO LÍQ. ACUM | OBSERVAÇÕES
    styles = getSampleStyleSheet()
    style_wrapped = copy(styles["Normal"])
    style_wrapped.fontSize = 8
    style_wrapped.leading = 9
    style_wrapped.textColor = colors.black

    style_header_col = copy(styles["Normal"])
    style_header_col.fontSize = 8
    style_header_col.leading = 9
    style_header_col.textColor = colors.white
    style_header_col.fontName = 'Helvetica-Bold'
    style_header_col.alignment = 2  # Right

    peso_liq_hdr = Paragraph("PESO LÍQ.<br/>ACUM", style_header_col)

    data = [["CÓDIGO", "CLIENTE", "N. FANTASIA", "MUNICÍPIO", "ORDEM", peso_liq_hdr, "OBSERVAÇÕES"]]

    for p in pedidos:
        cliente_p = Paragraph(str(p.cliente or ""), style_wrapped)
        fantasia_p = Paragraph(str(p.nome_fantasia or ""), style_wrapped)
        obs_p = Paragraph(str(p.obs_carga or ""), style_wrapped)

        data.append([
            str(p.codigo_cliente or p.id_pedido),
            cliente_p,
            fantasia_p,
            str(p.cidade or "")[:15],
            str(p.ordem_carregamento or ""),
            _br_number(p.peso_total_kg, 0),
            obs_p
        ])

    # 7 colunas: sem Peso Br. Acum
    table = Table(data, colWidths=[1.8*cm, 7.5*cm, 4.5*cm, 3.2*cm, 1.3*cm, 2.2*cm, 7.8*cm], repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),  # Peso Líq.
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
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
    sql_resumo = text("""SELECT 
            i.codigo as item_codigo,
            MAX(i.nome) as item_nome,
            SUM(i.quantidade) as qtd_total,
            MAX(i.embalagem) as item_embalagem,
            MAX(CAST(prod.peso AS FLOAT)) AS peso_unitario,
            MAX(CAST(COALESCE(prod.peso_bruto, prod.peso, 0) AS FLOAT)) AS peso_bruto_unitario,
            CAST(SUM(i.quantidade * COALESCE(prod.peso, 0)) AS FLOAT) AS peso_liquido_total,
            CAST(SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) AS FLOAT) AS peso_bruto_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        JOIN tb_pedidos_itens i ON i.id_pedido = p.id_pedido
        LEFT JOIN (
            SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto
            FROM t_cadastro_produto_v2
            GROUP BY codigo_supra
        ) prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, i.nome
        HAVING SUM(i.quantidade) > 0
        ORDER BY peso_liquido_total DESC""")
    produtos = db.execute(sql_resumo, {"cid": carga_id}).mappings().all()
    carga = db.execute(text("SELECT * FROM tb_cargas WHERE id = :cid"), {"cid": carga_id}).mappings().first()

    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    # Internal draw logic to reuse in Completo
    _desenhar_resumo_logic(c, db, carga, produtos, width, height)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def _desenhar_resumo_logic(c, db, carga, produtos, width, height, y_start=None):
    # Calcular totais antecipadamente para o cabeçalho
    total_liq = sum(getattr(p, 'peso_liquido_total', 0.0) or 0.0 for p in produtos)
    total_bruto = sum(getattr(p, 'peso_bruto_total', 0.0) or 0.0 for p in produtos)

    if y_start is None:
        y = _draw_header(c, width, height, "RESUMO DE PRODUTOS")
        # Header Info as per drawing 4: Filial | CARGA Nº | DATA
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(0.7*cm, y, f"Filial: SUPRA LOG")
        c.drawString(7.0*cm, y, f"CARGA Nº: {carga.get('numero_carga') or ''}")
        
        data_carregamento = carga.get('data_carregamento')
        data_str = data_carregamento.strftime('%d/%m/%Y') if data_carregamento else '____/____/____'
        c.drawRightString(width - 0.7*cm, y, f"DATA CARREGAMENTO: {data_str}")
        y -= 0.5*cm

        # Totais no cabeçalho — canto direito, acima da tabela
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(width - 0.7*cm, y, f"TOTAL P. LÍQ: {_br_number(total_liq, 0)} kg   |   TOTAL P. BRUTO: {_br_number(total_bruto, 0)} kg")
        y -= 0.8*cm
    else:
        y = y_start

    # Table columns: CÓDIGO | DESCRIÇÃO PRODUTO | EMBALAGEM | P. LÍQ. UN | QTD | P. LÍQ ACUM
    data = [["CÓDIGO", "DESCRIÇÃO PRODUTO", "EMBALAGEM", "P. LÍQ. UN", "QTD", "P. LÍQ ACUM"]]
    
    for p in produtos:
        peso_unit = getattr(p, 'peso_unitario', 0.0) or 0.0
        peso_total = getattr(p, 'peso_liquido_total', 0.0) or 0.0
        data.append([
            str(p.item_codigo),
            str(p.item_nome)[:50],
            str(p.item_embalagem or ""),
            _br_number(peso_unit, 0),
            str(int(p.qtd_total or 0)),
            _br_number(peso_total, 0),
        ])

    # Width distribution for portrait A4 (~21cm width - margins)
    col_widths = [2.2*cm, 8.5*cm, 2.5*cm, 2.2*cm, 1.5*cm, 2.7*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'), # P. LÍQ. UN
        ('ALIGN', (4, 0), (4, -1), 'CENTER'), # Qtd
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'), # P. LÍQ ACUM
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
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
        SELECT c.*, t.motorista, t.modelo, t.veiculo_placa, t.transportadora 
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
            p.codigo_cliente,
            COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente,
            c.cadastro_nome_fantasia as nome_fantasia,
            c.entrega_municipio as cidade,
            p.peso_total_kg,
            COALESCE(pb.peso_bruto_total, p.peso_total_kg) as peso_bruto_total,
            cp.observacoes as obs_carga
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN (
             SELECT 
                 id_pedido,
                 SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) as peso_bruto_total
             FROM tb_pedidos_itens i
             LEFT JOIN (
                 SELECT codigo_supra, MAX(peso) as peso, MAX(peso_bruto) as peso_bruto 
                 FROM t_cadastro_produto_v2 GROUP BY codigo_supra
             ) prod ON prod.codigo_supra = i.codigo
             GROUP BY id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
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
            MAX(CAST(prod.peso AS FLOAT)) AS peso_unitario,
            MAX(CAST(COALESCE(prod.peso_bruto, prod.peso, 0) AS FLOAT)) AS peso_bruto_unitario,
            CAST(SUM(i.quantidade * COALESCE(prod.peso, 0)) AS FLOAT) AS peso_liquido_total,
            CAST(SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) AS FLOAT) AS peso_bruto_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        JOIN tb_pedidos_itens i ON p.id_pedido = i.id_pedido
        LEFT JOIN (
            SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto
            FROM t_cadastro_produto_v2
            GROUP BY codigo_supra
        ) prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, i.nome
        HAVING SUM(i.quantidade) > 0
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
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.7*cm, y, f"Filial: SUPRA LOG")
    c.drawString(8.0*cm, y, f"CARGA Nº: {carga.get('numero_carga') or ''}")
    # Fix missing DATA CARREGAMENTO var definition issue
    data_carregamento = carga.get('data_carregamento')
    data_str = data_carregamento.strftime('%d/%m/%Y') if data_carregamento else '____/____/____'
    c.drawRightString(width - 0.7*cm, y, f"DATA CARREGAMENTO: {data_str}")
    y -= 0.5*cm

    # Calcular totais para o cabeçalho — canto direito
    t_liq = sum(getattr(p, 'peso_total_kg', 0.0) or 0.0 for p in pedidos)
    t_bru = sum(getattr(p, 'peso_bruto_total', 0.0) or 0.0 for p in pedidos)

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - 0.7*cm, y, f"TOTAL P. LÍQ: {_br_number(t_liq, 0)} kg   |   TOTAL P. BRUTO: {_br_number(t_bru, 0)} kg")
    y -= 0.6*cm
    
    c.drawString(0.7*cm, y, f"TRANSPORTADORA: {carga.get('transportadora') or 'Próprio'}")
    c.drawString(8.0*cm, y, f"MOTORISTA: {carga.get('motorista') or '-'}")
    c.drawRightString(width - 0.7*cm, y, f"VEÍCULO/PLACA: {carga.get('modelo') or '-'} / {carga.get('veiculo_placa') or '-'}")
    y -= 0.55*cm

    # Totais abaixo da linha do veículo — canto direito
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - 0.7*cm, y, f"TOTAL P. LÍQ: {_br_number(t_liq, 0)} kg   |   TOTAL P. BRUTO: {_br_number(t_bru, 0)} kg")
    y -= 0.8*cm

    styles = getSampleStyleSheet()
    style_wrapped = copy(styles["Normal"])
    style_wrapped.fontSize = 9
    style_wrapped.leading = 10
    style_wrapped.textColor = colors.black

    data = [["CÓDIGO", "CLIENTE", "N. FANTASIA", "MUNICÍPIO", "ORDEM CARREG.", "PESO LÍQ. ACUM", "OBSERVAÇÃO PEDIDO"]]
    for p in pedidos:
        cliente_p = Paragraph(str(p.cliente or ""), style_wrapped)
        fantasia_p = Paragraph(str(p.nome_fantasia or ""), style_wrapped)
        obs_p = Paragraph(str(p.obs_carga or ""), style_wrapped)

        peso_total_kg = getattr(p, 'peso_total_kg', 0.0) or 0.0

        data.append([
            str(p.codigo_cliente or p.id_pedido),
            cliente_p,
            fantasia_p,
            str(p.cidade or "")[:20],
            str(p.ordem_carregamento or ""),
            _br_number(peso_total_kg, 0),
            obs_p
        ])

    # 7 colunas: sem Peso Br. Acum
    table = Table(data, colWidths=[1.8*cm, 7.5*cm, 4.5*cm, 3.2*cm, 2.5*cm, 2.2*cm, 6.1*cm], repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUPRA_BAR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),  # Peso Líq.
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
