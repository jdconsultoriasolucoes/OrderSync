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

from services.pedido_pdf_data import carregar_pedido_pdf
from models.pedido_pdf import PedidoPdf

# Paleta de cores (bege / marrom)
SUPRA_RED = colors.HexColor("#C1AD99")        # cor principal (onde era vermelho)
SUPRA_DARK = colors.HexColor("#4A4036")      # texto escuro
SUPRA_BG_LIGHT = colors.HexColor("#F4EFE2")  # fundo claro para caixas


def _br_number(valor: float, casas: int = 2, sufixo: str = "") -> str:
    """
    Formata número no padrão brasileiro, ex: 1234.5 -> '1.234,50'
    """
    txt = f"{valor:,.{casas}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return txt + sufixo


def _desenhar_pdf(pedido: PedidoPdf, path: str) -> None:
    """
    Desenha o PDF do pedido no arquivo `path`, usando layout corporativo.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Página em modo paisagem (horizontal)
    pagesize = landscape(A4)
    c = canvas.Canvas(path, pagesize=pagesize)
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
        logo_env = os.getenv("ORDERSYNC_LOGO_PATH")
        if logo_env and Path(logo_env).exists():
            logo_path = Path(logo_env)
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
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception:
            logo_h = 0

    # Faixa superior logo abaixo do logo
    barra_altura = 0.9 * cm
    barra_top = top_y - logo_h - 0.05 * cm
    barra_bottom = barra_top - barra_altura

    c.setFillColor(SUPRA_RED)
    c.rect(0, barra_bottom, width, barra_altura, fill=1, stroke=0)

    # Título à esquerda
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    titulo_y = barra_bottom + 0.25 * cm
    c.drawString(margin_x, titulo_y, "DIGITAÇÃO DO ORÇAMENTO")

    # Data à direita
    c.setFont("Helvetica", 10)
    data_pedido = pedido.data_pedido
    if isinstance(data_pedido, datetime):
        data_str = data_pedido.strftime("%d/%m/%Y")
    else:
        data_str = ""
    c.drawRightString(width - margin_x, titulo_y, data_str)

    c.setFillColor(SUPRA_DARK)

    # =======================
    # DADOS BÁSICOS (2 BLOCOS)
    # =======================
    codigo_cliente = pedido.codigo_cliente or "Não cadastrado"
    cliente = pedido.cliente or ""
    frete_total = float(pedido.frete_total or 0)
    if pedido.data_entrega_ou_retirada:
        data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
    else:
        data_entrega_str = ""

    # Bloco 1: Código e Cliente na MESMA linha
    bloco1_data = [[
        "Código:", str(codigo_cliente),
        "Cliente:", cliente[:120],
    ]]

    # larguras: rótulos fixos e valores proporcionais
    label_cod_w = 2.5 * cm
    label_cli_w = 2.0 * cm
    restante = available_width - (label_cod_w + label_cli_w)
    cod_val_w = restante * 0.30
    cli_val_w = restante * 0.70
    bloco1_col_widths = [label_cod_w, cod_val_w, label_cli_w, cli_val_w]

    bloco1 = Table(bloco1_data, colWidths=bloco1_col_widths)
    bloco1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),  # "Código:"
                ("ALIGN", (1, 0), (1, 0), "LEFT"),    # valor código
                ("ALIGN", (2, 0), (2, 0), "CENTER"),  # "Cliente:"
                ("ALIGN", (3, 0), (3, 0), "LEFT"),    # valor cliente
            ]
        )
    )

    y = barra_bottom - 0.4 * cm
    _, b1_h = bloco1.wrap(available_width, height)
    bloco1.drawOn(c, margin_x, y - b1_h)
    y = y - b1_h

    # Bloco 2: Frete e Data em dois quadros separados
    bloco2_gap = 0.3 * cm
    bloco2_left_w = available_width * 0.45
    bloco2_right_w = available_width - bloco2_left_w - bloco2_gap

    frete_data = [["Valor Frete (TO):", "R$ " + _br_number(frete_total)]]
    data_data = [["Data da Entrega ou Retira:", data_entrega_str]]

    frete_col_widths = [bloco2_left_w * 0.5, bloco2_left_w * 0.5]
    data_col_widths = [bloco2_right_w * 0.55, bloco2_right_w * 0.45]

    frete_table = Table(frete_data, colWidths=frete_col_widths)
    frete_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ]
        )
    )

    data_table = Table(data_data, colWidths=data_col_widths)
    data_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ]
        )
    )

    y = y - 0.1 * cm
    _, frete_h = frete_table.wrap(bloco2_left_w, height)
    _, data_h = data_table.wrap(bloco2_right_w, height)
    bloco2_h = max(frete_h, data_h)

    frete_table.drawOn(c, margin_x, y - frete_h)
    data_table.drawOn(c, margin_x + bloco2_left_w + bloco2_gap, y - data_h)
    y = y - bloco2_h + -0.3 * cm

    # =======================
    # TABELA DE ITENS
    # =======================
    header = [
        "Codigo",
        "Produto",
        "Embalagem",
        "Qtd",
        "Cond. Pgto",
        "Comissão",
        "Valor Retira",
        "Valor Entrega",
    ]
    data = [header]

    for it in pedido.itens:
        data.append(
            [
                it.codigo,
                it.produto,
                it.embalagem or "",
                f"{it.quantidade:g}",
                it.condicao_pagamento or "",
                it.tabela_comissao or "",
                "R$ " + _br_number(float(it.valor_retira or 0)),
                "R$ " + _br_number(float(it.valor_entrega or 0)),
            ]
        )

    # Larguras base em cm; escala para ocupar a largura inteira
    base_widths_cm = [
        2.0,  # Código
        7.0,  # Produto
        2.5,  # Embalagem
        1.5,  # Qtd
        4.0,  # Cond. Pgto
        4.0,  # Comissão
        2.2,  # Valor Retira
        2.2,  # Valor Entrega
    ]
    total_base = sum(base_widths_cm)
    scale = (available_width / cm) / total_base
    col_widths = [w * scale * cm for w in base_widths_cm]

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
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
                ("ALIGN", (3, 1), (3, -1), "CENTER"),   # Qtd
                ("ALIGN", (6, 1), (7, -1), "RIGHT"),    # valores
            ]
        )
    )

    itens_x = margin_x
    _, table_height = table.wrap(available_width, height)
    table.drawOn(c, itens_x, y - table_height)
    y = y - table_height - 0.5 * cm

    # =======================
    # FECHAMENTO + OBSERVAÇÕES
    # =======================
    obs_text = (pedido.observacoes or "").strip()

    # largura dos dois blocos na mesma linha
    gap = 0.3 * cm
    fech_block_width = available_width * 0.45   # fechamento à esquerda
    obs_block_width = available_width - fech_block_width - gap

    # Fechamento do Orçamento (ESQUERDA)
    total_peso = float(pedido.total_peso_bruto or 0)
    total_valor = float(pedido.total_valor or 0)

    data_fech = [
        ["Fechamento do Orçamento:", ""],
        ["Total em Peso Bruto:", _br_number(total_peso, 3, " kg")],
        ["Total em Valor:", "R$ " + _br_number(total_valor)],
    ]

    fech_col_widths = [fech_block_width * 0.6, fech_block_width * 0.4]

    fech_table = Table(data_fech, colWidths=fech_col_widths)
    fech_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    # Observações (DIREITA, SEMPRE APARECE) – com quebra de linha automática
    obs_para = Paragraph(obs_text.replace("\n", "<br/>"), obs_style)

    data_obs = [["Observações:", obs_para]]
    obs_col_widths = [2.8 * cm, obs_block_width - 2.8 * cm]

    obs_table = Table(data_obs, colWidths=obs_col_widths)
    obs_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ]
        )
    )

    # desenha lado a lado na mesma "altura"
    y_top = y
    fech_x = itens_x
    obs_x = itens_x + fech_block_width + gap

    _, fech_h = fech_table.wrap(fech_block_width, height)
    _, obs_h = obs_table.wrap(obs_block_width, height)

    fech_table.drawOn(c, fech_x, y_top - fech_h)
    obs_table.drawOn(c, obs_x, y_top - obs_h)

    max_h = max(fech_h, obs_h)
    y = y_top - max_h - 0.3 * cm

    # rodapé
    c.setFont("Helvetica", 8)
    c.drawString(itens_x, y, "Documento gerado automaticamente pelo OrderSync.")

    c.showPage()
    c.save()


def gerar_pdf_pedido(*args, destino_dir: str = "/tmp", **kwargs):
    """
    Wrapper compatível com os dois jeitos de uso:

    1) JEITO ANTIGO:
        pedido_pdf = carregar_pedido_pdf(db, pedido_id)
        path_pdf = gerar_pdf_pedido(pedido_pdf)
        -> retorna STRING com o caminho do PDF

    2) JEITO NOVO:
        pdf_bytes = gerar_pdf_pedido(db, pedido_id)
        -> retorna BYTES do PDF (pronto pra anexar)
    """
    # permite sobrescrever destino_dir via kwargs
    if "destino_dir" in kwargs and kwargs["destino_dir"]:
        destino_dir = kwargs["destino_dir"]

    # Caso 1: gerar_pdf_pedido(pedido_pdf)
    if len(args) == 1 and isinstance(args[0], PedidoPdf):
        pedido = args[0]
        os.makedirs(destino_dir, exist_ok=True)
        path = os.path.join(destino_dir, f"pedido_{pedido.id_pedido}.pdf")
        _desenhar_pdf(pedido, path)
        return path

    # Caso 2: gerar_pdf_pedido(db, pedido_id)
    if len(args) >= 2:
        db = args[0]
        pedido_id = args[1]
    elif "db" in kwargs and "pedido_id" in kwargs:
        db = kwargs["db"]
        pedido_id = kwargs["pedido_id"]
    else:
        raise TypeError("Uso inválido de gerar_pdf_pedido")

    pedido = carregar_pedido_pdf(db, int(pedido_id))
    os.makedirs(destino_dir, exist_ok=True)
    path = os.path.join(destino_dir, f"pedido_{pedido.id_pedido}.pdf")
    _desenhar_pdf(pedido, path)

    # no jeito novo, devolve bytes (pra anexo de e-mail)
    with open(path, "rb") as f:
        return f.read()
