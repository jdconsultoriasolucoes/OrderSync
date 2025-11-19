# backend/services/pdf_service.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from pathlib import Path
import os

from services.pedido_pdf_data import carregar_pedido_pdf
from models.pedido_pdf import PedidoPdf

# Cor principal da Supra (pode ajustar se quiser outro tom)
SUPRA_RED = colors.HexColor("#B3001F")
SUPRA_DARK = colors.black


def _br_number(valor: float, casas: int = 2, sufixo: str = "") -> str:
    """
    Formata número no padrão brasileiro, ex: 1234.5 -> '1.234,50'
    """
    txt = f"{valor:,.{casas}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return txt + sufixo


def _desenhar_pdf(pedido: PedidoPdf, path: str) -> None:
    """
    Desenha o PDF do pedido no arquivo `path`,
    usando layout corporativo com identidade da Supra.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # margens menores e tudo mais "colado" à esquerda
    margin_x = 0.7 * cm
    margin_y = 1.0 * cm
    top_y = height - margin_y
    available_width = width - 2 * margin_x

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
            logo_w = 3.0 * cm  # tamanho discreto
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
            logo_h = 0  # se der erro no logo, segue sem

    # Faixa vermelha logo abaixo do logo
    barra_altura = 0.9 * cm
    barra_top = top_y - logo_h - 0.2 * cm
    barra_bottom = barra_top - barra_altura

    c.setFillColor(SUPRA_RED)
    c.rect(0, barra_bottom, width, barra_altura, fill=1, stroke=0)

    # Título alinhado à esquerda e encostado na parte de baixo da faixa
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    titulo_y = barra_bottom + 0.25 * cm
    c.drawString(margin_x, titulo_y, "DIGITAÇÃO DO ORÇAMENTO")

    # Data à direita dentro da faixa
    c.setFont("Helvetica", 10)
    data_pedido = pedido.data_pedido
    if isinstance(data_pedido, datetime):
        data_str = data_pedido.strftime("%d/%m/%Y")
    elif data_pedido:
        data_str = data_pedido.strftime("%d/%m/%Y")
    else:
        data_str = ""
    c.drawRightString(width - margin_x, titulo_y, data_str)

    # volta cor padrão texto
    c.setFillColor(SUPRA_DARK)

    # =======================
    # BLOCO CABEÇALHO COM BORDA
    # =======================
    codigo_cliente = pedido.codigo_cliente or "Não cadastrado"
    cliente = pedido.cliente or ""

    frete_total = float(pedido.frete_total or 0)

    if pedido.data_entrega_ou_retirada:
        data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
    else:
        data_entrega_str = ""

    # tabela de 2 linhas x 4 colunas, com borda ao redor
    header_data = [
        ["Codigo:", str(codigo_cliente), "Cliente:", cliente[:80]],
        ["Valor Frete (TO):", "R$ " + _br_number(frete_total), "Data da Entrega ou Retira:", data_entrega_str],
    ]

    header_col_widths = [
        available_width * 0.12,
        available_width * 0.23,
        available_width * 0.20,
        available_width * 0.45,
    ]

    header_table = Table(header_data, colWidths=header_col_widths)
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )

    # posição: logo abaixo da faixa
    y = barra_bottom - 0.5 * cm
    header_w, header_h = header_table.wrap(available_width, height)
    header_table.drawOn(c, margin_x, y - header_h)
    y = y - header_h - 0.8 * cm

    # =======================
    # TABELA DE ITENS
    # =======================
    header = [
        "Codigo",
        "Produto",
        "Embalagem",
        "Qtd",
        "Cond. Pgto",
        "Comissão",          # <--- trocado aqui
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

    col_widths = [
        1.8 * cm,  # Código
        5.0 * cm,  # Produto
        2.0 * cm,  # Embalagem
        1.4 * cm,  # Qtd
        2.5 * cm,  # Cond. Pgto
        1.8 * cm,  # Comissão (menor)
        2.1 * cm,  # Valor Retira
        2.1 * cm,  # Valor Entrega
    ]

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                # cabeçalho
                ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                # bordas e linhas
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # alinhamentos
                ("ALIGN", (3, 1), (3, -1), "CENTER"),   # Qtd
                ("ALIGN", (6, 1), (7, -1), "RIGHT"),    # Valores
            ]
        )
    )

    table_width, table_height = table.wrap(available_width, height)
    table.drawOn(c, margin_x, y - table_height)
    y = y - table_height - 0.8 * cm

    # =======================
    # FECHAMENTO DO ORÇAMENTO (COM BORDA)
    # =======================
    total_peso = float(pedido.total_peso_bruto or 0)
    total_valor = float(pedido.total_valor or 0)

    data_fech = [
        ["Fechamento do Orçamento:", ""],
        ["Total em Peso Bruto:", _br_number(total_peso, 3, " kg")],
        ["Total em Valor:", "R$ " + _br_number(total_valor)],
    ]

    fech_table = Table(data_fech, colWidths=[6.0 * cm, 5.0 * cm])
    fech_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    fech_w, fech_h = fech_table.wrap(available_width, height)
    fech_table.drawOn(c, margin_x, y - fech_h)
    y = y - fech_h - 0.5 * cm

    # rodapé
    c.setFont("Helvetica", 8)
    c.drawString(margin_x, y, "Documento gerado automaticamente pelo OrderSync.")

    c.showPage()
    c.save()


def gerar_pdf_pedido(*args, destino_dir: str = "/tmp", **kwargs):
    """
    Wrapper compatível com os dois jeitos de uso:

    1) JEITO ANTIGO (ainda pode existir em algum lugar do código):
        pedido_pdf = carregar_pedido_pdf(db, pedido_id)   # ou outra função
        path_pdf = gerar_pdf_pedido(pedido_pdf)
        -> retorna STRING com o caminho do PDF

    2) JEITO NOVO (que usamos na confirmação para anexo de e-mail):
        pdf_bytes = gerar_pdf_pedido(db, pedido_id)
        -> retorna BYTES do PDF (pronto pra anexar)
    """
    # permite sobrescrever destino_dir via kwargs
    if "destino_dir" in kwargs and kwargs["destino_dir"]:
        destino_dir = kwargs["destino_dir"]

    # -------------------------
    # Caso 1: gerar_pdf_pedido(pedido_pdf)
    # -------------------------
    if len(args) == 1 and isinstance(args[0], PedidoPdf):
        pedido = args[0]
        os.makedirs(destino_dir, exist_ok=True)
        path = os.path.join(destino_dir, f"pedido_{pedido.id_pedido}.pdf")
        _desenhar_pdf(pedido, path)
        return path

    # -------------------------
    # Caso 2: gerar_pdf_pedido(db, pedido_id)
    # -------------------------
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
