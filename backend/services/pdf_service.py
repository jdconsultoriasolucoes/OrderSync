# backend/services/pdf_service.py

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from pathlib import Path
import os
import io

from services.pedido_pdf_data import carregar_pedido_pdf
from models.pedido_pdf import PedidoPdf


# Paleta de cores
SUPRA_RED = colors.Color(0.78, 0.70, 0.60)       # faixa e cabeçalho da tabela
SUPRA_DARK = colors.Color(0.1, 0.1, 0.1)        # texto escuro
SUPRA_BG_LIGHT = colors.Color(0.95, 0.95, 0.95) # fundo clarinho


def _br_number(value, decimals=2, suffix=""):
    """
    Formata número no padrão brasileiro.
    """
    if value is None:
        value = 0
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    fmt = f"{{:,.{decimals}f}}"
    s = fmt.format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s + suffix


def _desenhar_pdf(pedido: PedidoPdf, buffer: io.BytesIO, sem_validade: bool = False) -> None:
    """
    Desenha o PDF do pedido no arquivo `path`, usando layout corporativo.
    """
    # Página em modo paisagem (horizontal)
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    # margens
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm
    top_y = height - margin_y
    available_width = width - 2 * margin_x

    # estilo para textos longos (Observações)
    styles = getSampleStyleSheet()
    obs_style = styles["Normal"]
    obs_style.fontName = "Helvetica"
    obs_style.fontSize = 9
    obs_style.leading = 11

    # ============================
    # LOGO EM CIMA / FAIXA EMBAIXO
    # ============================
    base_dir = Path(__file__).resolve().parents[2]
    logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png"

    if not logo_path.exists():
        # fallback genérico
        static_dir = base_dir / "frontend" / "public"
        for candidate in [
            static_dir / "logo_cliente_supra.png",
            static_dir / "logo.png",
        ]:
            if candidate.exists():
                logo_path = candidate
                break
        else:
            logo_path = None

    # Logo no canto direito superior (acima da faixa)
    logo_h = 0
    if logo_path and logo_path.exists():
        try:
            img = ImageReader(str(logo_path))
            logo_w = 3.0 * cm
            iw, ih = img.getSize()
            logo_h = logo_w * ih / iw
            x_logo = width - margin_x - logo_w
            y_logo = top_y - logo_h
            c.drawImage(
                img,
                x_logo,
                y_logo,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            logo_h = 0

    # Faixa horizontal (header corporativo)
    faixa_h = 1.2 * cm
    faixa_y = top_y - logo_h - 0.2 * cm
    c.setFillColor(SUPRA_RED)
    c.rect(margin_x, faixa_y - faixa_h, available_width, faixa_h, stroke=0, fill=1)

    # Texto na faixa com número do Pedido do Sistema recolocado
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(
        margin_x + 0.3 * cm,
        faixa_y - faixa_h + 0.62 * cm,
        f"DIGITAÇÃO DO ORÇAMENTO (Nº: {pedido.id_pedido})"
    )

    # Data / Validade (Bloco direito do header)
    c.setFont("Helvetica", 10)
    c.drawRightString(width - margin_x, faixa_y - faixa_h + 0.5 * cm, f"Data do Pedido: {pedido.data_pedido.strftime('%d/%m/%Y')}")
    
    if sem_validade:
        validade_str = "Consulte o vendedor"
        if pedido.validade_tabela:
             validade_str = pedido.validade_tabela
        
        c.drawRightString(width - margin_x, faixa_y - faixa_h + 0.1 * cm, f"Validade da Proposta: {validade_str}")
    else:
        if pedido.validade_tabela:
            c.drawRightString(width - margin_x, faixa_y - faixa_h + 0.1 * cm, f"Proposta válida até: {pedido.validade_tabela}")
        else:
            c.drawRightString(width - margin_x, faixa_y - faixa_h + 0.1 * cm, "Proposta válida até: Não se aplica")

    # Atualiza y para baixo da faixa
    y = faixa_y - faixa_h - 0.5 * cm

    # =======================
    # BLOCO 1 - DADOS CLIENTE
    # =======================
    codigo_cliente = pedido.codigo_cliente or ""
    cliente = pedido.cliente or ""
    razao_social = pedido.razao_social or pedido.nome_fantasia or ""

    if sem_validade:
        # Layout Cliente: Sem Código do Cliente no Header
        label_cli_w = 2.0 * cm
        label_raz_w = 2.3 * cm
        restante    = available_width - (label_cli_w + label_raz_w)
        cli_val_w   = max(restante * 0.55, 6.0 * cm)
        raz_val_w   = max(restante * 0.45, 5.0 * cm)

        bloco1_col_widths = [
            label_cli_w, cli_val_w,
            label_raz_w, raz_val_w,
        ]
        bloco1_data = [[
            "Cliente:", cliente[:120],
            "Razão Social:", razao_social[:80],
        ]]
    else:
        label_cod_w = 1.4 * cm
        cod_val_w   = 3.5 * cm 
        label_cli_w = 2.0 * cm
        label_raz_w = 2.3 * cm
        restante    = available_width - (label_cod_w + cod_val_w + label_cli_w + label_raz_w)
        cli_val_w   = max(restante * 0.55, 6.0 * cm)
        raz_val_w   = max(restante * 0.45, 5.0 * cm)

        bloco1_col_widths = [
            label_cod_w, cod_val_w,
            label_cli_w, cli_val_w,
            label_raz_w, raz_val_w,
        ]
        bloco1_data = [[
            "Código:", str(codigo_cliente),
            "Cliente:", cliente[:120],
            "Razão Social:", razao_social[:80],
        ]]

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), SUPRA_BG_LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]

    if sem_validade:
        style_cmds.extend([
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),  # "Cliente:"
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),  # "Razão Social:"
        ])
    else:
        style_cmds.extend([
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),  # "Código:"
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),  # "Cliente:"
            ("ALIGN", (4, 0), (4, 0), "RIGHT"),  # "Razão Social:"
        ])

    bloco1_table = Table(bloco1_data, colWidths=bloco1_col_widths)
    bloco1_table.setStyle(TableStyle(style_cmds))

    _, bloco1_h = bloco1_table.wrap(available_width, height)
    bloco1_table.drawOn(c, margin_x, y - bloco1_h)
    y = y - bloco1_h - 0.3 * cm

    # =======================
    # BLOCO 2 - FRETE / DATA (HORIZONTAL ÚNICO)
    # =======================
    frete_total = float(pedido.frete_total or 0)
    frete_kg = float(pedido.frete_kg or 0)

    if pedido.data_entrega_ou_retirada:
        data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
    else:
        data_entrega_str = ""

    if frete_total > 0:
        frete_str = "R$ " + _br_number(frete_total)
    else:
        frete_str = "R$ 0,00"

    # Criando a tabela horizontal unificada abrangendo a largura inteira (available_width)
    if sem_validade:
        # Versão Cliente: Mostra apenas a Data de Retirada/Entrega
        bloco2_data = [["", "", "", "", "Data Retirada/Entrega:", data_entrega_str]]
    else:
        # Versão Vendedor: Mostra Ped. Supra (esquerda), Frete Total (meio) e Data (direita)
        ped_supra_val = pedido.pedido_supra or ""
        bloco2_data = [["Ped. Supra:", ped_supra_val, "Frete Total:", frete_str, "Data Retirada/Entrega:", data_entrega_str]]

    # Proporções alinhando Ped. Supra na esquerda, Frete Total no meio, e Data na direita
    col0 = 2.5 * cm
    col1 = 3.5 * cm
    col2 = 2.5 * cm
    col3 = 3.5 * cm
    col4 = 4.5 * cm
    col5 = available_width - (col0 + col1 + col2 + col3 + col4)

    bloco2_col_widths = [col0, col1, col2, col3, col4, col5]

    bloco2_style = [
        ("BACKGROUND", (0, 0), (-1, -1), SUPRA_BG_LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (0, 0), (0, 0), "RIGHT"),  # "Ped. Supra:" label
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),  # "Frete Total:" label
        ("ALIGN", (4, 0), (4, 0), "RIGHT"),  # "Data Retirada/Entrega:" label
    ]

    if sem_validade:
        # Remove fundo das colunas ocultas e aplica grid apenas no bloco de data (colunas 4 e 5)
        bloco2_style.append(("BACKGROUND", (0, 0), (3, 0), colors.white))
        bloco2_style.append(("GRID", (4, 0), (5, 0), 0.5, colors.black))
        bloco2_style.append(("BOX", (4, 0), (5, 0), 0.5, colors.black))
    else:
        bloco2_style.append(("GRID", (0, 0), (-1, -1), 0.5, colors.black))
        bloco2_style.append(("BOX", (0, 0), (-1, -1), 0.5, colors.black))

    bloco2_table = Table(bloco2_data, colWidths=bloco2_col_widths)
    bloco2_table.setStyle(TableStyle(bloco2_style))

    y = y - 0.1 * cm
    _, bloco2_h = bloco2_table.wrap(available_width, height)
    bloco2_table.drawOn(c, margin_x, y - bloco2_h)
    y = y - bloco2_h - 0.5 * cm

    # =======================
    # TABELA DE ITENS (multi-página)
    # =======================
    header = [
        "#",
        "Fornecedor",
        "Codigo",
        "Produto",
        "Embal",
        "Qtd",
        "Cond. Pgto",
        "Comissão",
        "Valor Retira",
        "Vl. Frete",
        "Valor Entrega",
    ]

    itens_ordenados = sorted(
        pedido.itens,
        key=lambda it: float(getattr(it, "quantidade", 0) or 0),
        reverse=True,
    )

    base_widths_cm = [
        0.8,  # Item (#)
        2.5,  # Fornecedor
        1.7,  # Código
        6.5,  # Produto
        1.5,  # Embalagem
        1.5,  # Qtd
        5.5,  # Cond. Pgto
        2.0,  # Comissão
        2.2,  # Valor Retira
        1.8,  # Vl. Frete
        2.2,  # Valor Entrega
    ]

    total_base = sum(base_widths_cm)
    scale = (available_width / cm) / total_base
    col_widths = [w * scale * cm for w in base_widths_cm]

    all_rows = []
    style_normal = styles["Normal"]
    style_normal.fontSize = 8
    style_normal.leading = 9

    for idx, it in enumerate(itens_ordenados, start=1):
        p_fornecedor = Paragraph(it.fornecedor or "", style_normal)
        p_produto = Paragraph(it.produto or "", style_normal)
        p_condicao = Paragraph(it.condicao_pagamento or "", style_normal)
        
        all_rows.append([
            str(idx),
            p_fornecedor,
            it.codigo,
            p_produto,
            it.embalagem or "",
            f"{it.quantidade:g}",
            p_condicao,
            it.tabela_comissao or "",
            "R$ " + _br_number(float(it.valor_retira or 0)),
            "R$ " + _br_number(float(it.valor_frete_unitario or 0)),
            "R$ " + _br_number(float(it.valor_entrega or 0)),
        ])

    itens_table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (4, 1), (4, -1), "CENTER"),   # Qtd
            ("ALIGN", (7, 1), (8, -1), "RIGHT"),    # valores
            ("ALIGN", (0, 1), (0, -1), "CENTER"),   # (#) Item
            ("ALIGN", (1, 1), (1, -1), "CENTER"),   # Fornecedor
        ]
    )

    itens_x = margin_x
    current_y = y

    def _desenhar_tabela_pagina(rows, y_top):
        if not rows:
            return y_top
        data_page = [header] + rows
        table = Table(data_page, colWidths=col_widths)
        table.setStyle(itens_table_style)
        _, table_height = table.wrap(available_width, height)
        table.drawOn(c, itens_x, y_top - table_height)
        return y_top - table_height - 0.5 * cm

    rows_buffer = []

    for row in all_rows:
        teste_rows = rows_buffer + [row]
        data_test = [header] + teste_rows
        table_test = Table(data_test, colWidths=col_widths)
        table_test.setStyle(itens_table_style)
        _, test_height = table_test.wrap(available_width, height)

        if current_y - test_height < margin_y:
            current_y = _desenhar_tabela_pagina(rows_buffer, current_y)
            rows_buffer = []
            c.showPage()
            current_y = height - margin_y

        rows_buffer.append(row)

    current_y = _desenhar_tabela_pagina(rows_buffer, current_y)
    y = current_y

    # =======================
    # FECHAMENTO + OBSERVAÇÕES
    # =======================
    obs_text = (pedido.observacoes or "").strip()

    gap = 0.3 * cm
    fech_block_width = available_width * 0.45
    obs_block_width = available_width - fech_block_width - gap

    total_peso_liq_raw = getattr(pedido, "total_peso_liquido", 0.0) or 0.0
    total_peso_bru_raw = getattr(pedido, "total_peso_bruto", 0.0) or 0.0

    def _fmt_peso(p):
        return _br_number(int(p + 0.5) if p >= 0 else int(p - 0.5), 0, " kg")

    total_valor = float(pedido.total_valor or 0)

    data_fech = [
        ["Fechamento do Orçamento:", ""],
    ]
    if not sem_validade:
        data_fech.append(["Total em Peso Líquido:", _fmt_peso(total_peso_liq_raw)])
        
    data_fech.append(["Total em Peso Bruto:", _fmt_peso(total_peso_bru_raw)])
    
    # Removido Pedido Supra daqui de acordo com a homologação
    data_fech.append(["Valor Frete:", "R$ " + _br_number(frete_total)])
    data_fech.append(["Total em Valor:", "R$ " + _br_number(total_valor)])

    t_fech = Table(data_fech, colWidths=[fech_block_width * 0.6, fech_block_width * 0.4])
    t_fech.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    
    t_obs = Table([
        ["Observações:", obs_text]
    ], colWidths=[2.5 * cm, obs_block_width - 2.5 * cm])
    t_obs.setStyle(TableStyle([
         ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
         ("BACKGROUND", (0, 0), (0, 0), colors.lightgrey),
         ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
         ("FONTSIZE", (0, 0), (-1, -1), 8),
         ("VALIGN", (0, 0), (-1, -1), "TOP"),
         ("ALIGN", (0, 0), (0, 0), "LEFT"),
    ]))

    w_f, h_f = t_fech.wrap(fech_block_width, height)
    w_o, h_o = t_obs.wrap(obs_block_width, height)
    needed_height = max(h_f, h_o) + 1.0 * cm

    if y - needed_height < margin_y:
        c.showPage()
        y = height - margin_y
    
    t_fech.wrapOn(c, fech_block_width, height)
    t_fech.drawOn(c, margin_x, y - h_f)

    t_obs.wrapOn(c, obs_block_width, height)
    t_obs.drawOn(c, margin_x + fech_block_width + gap, y - h_o)
    
    if sem_validade:
        c.saveState()
        c.setFont("Helvetica-Bold", 60)
        c.setFillColor(colors.Color(0.8, 0.8, 0.8, alpha=0.3))
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "ORÇAMENTO")
        c.restoreState()

    c.showPage()
    try:
        c.save()
    except Exception as e:
        if "can only be saved once" in str(e):
            pass
        else:
            raise e


def gerar_pdf_pedido(*args, destino_dir: str = "/tmp", sem_validade: bool = False, **kwargs) -> bytes:
    pedido = None
    
    if len(args) == 1:
        if isinstance(args[0], PedidoPdf):
            pedido = args[0]
    
    if not pedido and len(args) >= 2:
        db = args[0]
        pid = args[1]
        pedido = carregar_pedido_pdf(db, int(pid))
        
    if not pedido and "db" in kwargs and "pedido_id" in kwargs:
         pedido = carregar_pedido_pdf(kwargs["db"], int(kwargs["pedido_id"]))
 
    if not pedido:
         if len(args) > 0 and isinstance(args[0], PedidoPdf):
             pedido = args[0]
         else:
             raise TypeError("Uso inválido de gerar_pdf_pedido. Esperado (PedidoPdf) ou (db, id).")

    if "sem_validade" in kwargs:
        sem_validade = kwargs["sem_validade"]

    if sem_validade:
        from services.pdf_cliente_layout import gerar_pdf_cliente_simplificado
        return gerar_pdf_cliente_simplificado(pedido)
    else:
        buffer = io.BytesIO()
        _desenhar_pdf(pedido, buffer, sem_validade=False)
        buffer.seek(0)
        return buffer.read()


def gerar_pdf_lista_preco(pedido: PedidoPdf, modo_frete: str = "ambos") -> bytes:
    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm

    base_dir = Path(__file__).resolve().parents[2]
    logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png"

    if not logo_path.exists():
        static_dir = base_dir / "frontend" / "public"
        for candidate in [
            static_dir / "logo_cliente_supra.png",
            static_dir / "logo.png",
        ]:
            if candidate.exists():
                logo_path = candidate
                break
        else:
            logo_path = None

    logo_h = 0
    if logo_path and logo_path.exists():
        try:
            img = ImageReader(str(logo_path))
            logo_w = 3.0 * cm
            iw, ih = img.getSize()
            logo_h = logo_w * ih / iw
            
            x_logo = width - margin_x - logo_w
            y_logo = height - margin_y - logo_h
            
            c.drawImage(
                img,
                x_logo,
                y_logo,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            logo_h = 0

    top_contect_y = height - margin_y
    if logo_h > 0:
        top_contect_y = top_contect_y - logo_h - 0.2 * cm

    c.setFillColor(SUPRA_RED)
    faixa_h = 1.0 * cm
    faixa_y = top_contect_y - faixa_h
    available_width = width - 2 * margin_x
    
    c.rect(margin_x, faixa_y, available_width, faixa_h, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    
    titulo_map = {
        "com": "LISTA DE PREÇOS (COM FRETE)",
        "sem": "LISTA DE PREÇOS (SEM FRETE)",
        "ambos": "LISTA DE PREÇOS"
    }
    titulo = titulo_map.get(modo_frete, "LISTA DE PREÇOS")
    c.drawString(margin_x + 0.3 * cm, faixa_y + 0.35 * cm, titulo)

    c.setFont("Helvetica", 9)
    data_str = pedido.data_pedido.strftime('%d/%m/%Y')
    
    right_text_x = width - margin_x - 0.3 * cm
    c.drawRightString(right_text_x, faixa_y + 0.6 * cm, f"Data: {data_str}")
    
    if pedido.validade_tabela:
        c.drawRightString(right_text_x, faixa_y + 0.2 * cm, f"Proposta válida até: {pedido.validade_tabela}")

    y = faixa_y - 0.5 * cm
    c.setFillColor(SUPRA_DARK)
    c.setFont("Helvetica-Bold", 9)
    
    c.drawString(margin_x, y, f"Cliente: {pedido.cliente or ''}") 
    if pedido.nome_fantasia:
         c.drawString(margin_x, y - 0.4*cm, f"Fantasia: {pedido.nome_fantasia}")
         y -= 0.4*cm
    
    y -= 0.8 * cm
    
    cols_def = [
        {"name": "Cód", "width": 1.2, "align": "CENTER"},
        {"name": "Produto", "width": 5.0, "align": "LEFT"}, 
        {"name": "Emb", "width": 1.1, "align": "CENTER"}, 
        {"name": "Condição", "width": 2.5, "align": "CENTER"}, 
    ]
    
    if modo_frete == "com":
        cols_def.append({"name": "R$ C/ Frete", "width": 2.0, "align": "CENTER"})
    elif modo_frete == "sem":
        cols_def.append({"name": "R$ S/Frete", "width": 2.0, "align": "CENTER"})
    else:
        cols_def.append({"name": "R$ C/ Frete", "width": 1.8, "align": "CENTER"})
        cols_def.append({"name": "R$ S/Frete", "width": 1.8, "align": "CENTER"})

    has_markup = any(float(it.markup or 0) > 0 for it in pedido.itens)

    if has_markup:
        cols_def.append({"name": "MKP %", "width": 1.2, "align": "CENTER"})
        if modo_frete == "com":
            cols_def.append({"name": "MKP C/Frete", "width": 2.2, "align": "CENTER"})
        elif modo_frete == "sem":
            cols_def.append({"name": "MKP S/Frete", "width": 2.2, "align": "CENTER"})
        else:
            cols_def.append({"name": "MKP C/Frete", "width": 2.0, "align": "CENTER"})
            cols_def.append({"name": "MKP S/Frete", "width": 2.0, "align": "CENTER"})
    else:
        for col in cols_def:
            if col["name"] == "Produto": col["width"] += 2.0
            if col["name"] == "Condição": col["width"] += 1.4

    header = [c["name"] for c in cols_def]
    
    base_total = sum(c["width"] for c in cols_def)
    scale = available_width / (base_total * cm)
    col_widths = [(c["width"] * scale) * cm for c in cols_def]
    
    align_styles = []
    for idx, col in enumerate(cols_def):
        align_styles.append(("ALIGN", (idx, 0), (idx, -1), col["align"]))

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ] + align_styles)

    itens_ordenados = sorted(pedido.itens, key=lambda it: it.produto or "")

    data_rows = []
    for it in itens_ordenados:
        markup_pct = it.markup or 0
        mk_str = f"{markup_pct:g}%" if markup_pct else "0%"
        
        custo_cf = float(it.valor_entrega or 0)
        custo_sf = float(it.valor_retira or 0)
        
        venda_cf = float(it.valor_final_markup or 0)
        venda_sf = float(it.valor_s_frete_markup or 0)
        
        if venda_cf <= 0: venda_cf = custo_cf
        if venda_sf <= 0: venda_sf = custo_sf

        row = [
            it.codigo or "",
            (it.produto or "")[:35],
            (it.embalagem or "")[:10],
            (it.condicao_pagamento or "")[:20],
        ]

        if modo_frete == "com":
            row.append(_br_number(custo_cf))
        elif modo_frete == "sem":
            row.append(_br_number(custo_sf))
        else:
            row.append(_br_number(custo_cf))
            row.append(_br_number(custo_sf))

        if has_markup:
            row.append(mk_str)
            if modo_frete == "com":
                row.append(_br_number(venda_cf))
            elif modo_frete == "sem":
                row.append(_br_number(venda_sf))
            else:
                row.append(_br_number(venda_cf))
                row.append(_br_number(venda_sf))

        data_rows.append(row)
    
    rows_buffer = []
    current_y = y
    
    def _draw_page(rows, y_pos):
        tbl = Table([header] + rows, colWidths=col_widths)
        tbl.setStyle(table_style)
        _, h_tbl = tbl.wrap(available_width, height)
        tbl.drawOn(c, margin_x, y_pos - h_tbl)
        return y_pos - h_tbl

    for row in data_rows:
        test_tbl = Table([header] + rows_buffer + [row], colWidths=col_widths)
        test_tbl.setStyle(table_style)
        _, h_test = test_tbl.wrap(available_width, height)
        
        if current_y - h_test < margin_y:
            _draw_page(rows_buffer, current_y)
            c.showPage()
            current_y = height - margin_y
            rows_buffer = [row]
        else:
            rows_buffer.append(row)

    if rows_buffer:
        _draw_page(rows_buffer, current_y)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
