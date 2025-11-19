# services/pdf_service.py
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


# cor “principal” da Supra (ajusta se quiser outro tom)
SUPRA_RED = colors.HexColor("#B3001F")
SUPRA_DARK = colors.black


def _br_number(valor: float, casas: int = 2, sufixo: str = "") -> str:
    txt = f"{valor:,.{casas}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return txt + sufixo


def gerar_pdf_pedido(db, pedido_id: int, destino_dir: str = "/tmp") -> bytes:
    """
    Gera o PDF do pedido no layout 'Digitação do Orçamento',
    usando as cores do cliente e incluindo o logo da Supra.
    Retorna os bytes do arquivo para anexar no e-mail.
    """
    # 1) Carregar dados consolidados
    pedido = carregar_pedido_pdf(db, pedido_id)

    os.makedirs(destino_dir, exist_ok=True)
    filename = f"pedido_{pedido.id_pedido}.pdf"
    path = os.path.join(destino_dir, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin_x = 2 * cm
    margin_y = 2 * cm
    y = height - margin_y

    # ==== LOGO SUPRA + BARRA SUPERIOR ====
    # tenta achar o logo em frontend/public/tabela_preco/logo.png
    base_dir = Path(__file__).resolve().parents[2]
    logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo.png"
    if not logo_path.exists():
        # fallback: se você preferir usar outro caminho, ajusta aqui
        logo_env = os.getenv("ORDERSYNC_LOGO_PATH")
        if logo_env and Path(logo_env).exists():
            logo_path = Path(logo_env)
        else:
            logo_path = None

    barra_altura = 1.2 * cm
    # barra colorida atrás do título
    c.setFillColor(SUPRA_RED)
    c.rect(0, y - barra_altura + 0.2 * cm, width, barra_altura, fill=1, stroke=0)

    # logo no canto esquerdo, em cima da barra
    if logo_path and logo_path.exists():
        try:
            img = ImageReader(str(logo_path))
            logo_w = 3.5 * cm
            iw, ih = img.getSize()
            logo_h = logo_w * ih / iw
            c.drawImage(
                img,
                margin_x,
                y - logo_h + 0.3 * cm,
                width=logo_w,
                height=logo_h,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception:
            # se der pau no logo, só ignora e segue a vida
            pass

    # título centralizado em branco
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "DIGITAÇÃO DO ORÇAMENTO")

    # data no canto direito
    c.setFont("Helvetica", 10)
    data_pedido = pedido.data_pedido
    if isinstance(data_pedido, datetime):
        data_str = data_pedido.strftime("%d/%m/%Y")
    elif data_pedido:
        data_str = data_pedido.strftime("%d/%m/%Y")
    else:
        data_str = ""
    c.drawRightString(width - margin_x, y - 0.1 * cm, data_str)

    # volta a cor de texto padrão
    c.setFillColor(SUPRA_DARK)

    y -= 1.6 * cm

    # ==== LINHA CÓDIGO / CLIENTE ====
    codigo_cliente = pedido.codigo_cliente or "Não cadastrado"
    cliente = pedido.cliente or ""

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Codigo:")
    c.setFont("Helvetica", 10)
    c.drawString(margin_x + 38, y, str(codigo_cliente))

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x + 160, y, "Cliente:")
    c.setFont("Helvetica", 10)
    c.drawString(margin_x + 210, y, cliente[:80])

    y -= 0.9 * cm

    # ==== LINHA FRETE / DATA ENTREGA ou RETIRA ====
    frete_total = float(pedido.frete_total or 0)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Valor Frete (TO):")
    c.setFont("Helvetica", 10)
    c.drawString(margin_x + 95, y, "R$ " + _br_number(frete_total))

    c.setFont("Helvetica-Bold", 10)
    label = "Data da Entrega ou Retira:"
    c.drawString(width / 2, y, label)

    if pedido.data_entrega_ou_retirada:
        data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
    else:
        data_entrega_str = ""
    c.setFont("Helvetica", 10)
    c.drawString(width / 2 + 150, y, data_entrega_str)

    y -= 1.2 * cm

    # ==== TABELA DE ITENS ====
    header = [
        "Codigo",
        "Produto",
        "Embalagem",
        "Qtd",
        "Cond. Pgto",
        "Tabela de Comissão",
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
        1.5 * cm,  # Qtd
        2.7 * cm,  # Cond. Pgto
        2.7 * cm,  # Tabela Comissão
        2.0 * cm,  # Valor Retira
        2.0 * cm,  # Valor Entrega
    ]

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                # cabeçalho com cor da Supra
                ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                # linhas da tabela
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (3, 1), (3, -1), "CENTER"),
                ("ALIGN", (6, 1), (7, -1), "RIGHT"),
            ]
        )
    )

    available_width = width - 2 * margin_x
    table_width, table_height = table.wrap(available_width, height)
    table.drawOn(c, margin_x, y - table_height)
    y = y - table_height - 1.0 * cm

    # ==== FECHAMENTO DO ORÇAMENTO ====
    total_peso = float(pedido.total_peso_bruto or 0)
    total_valor = float(pedido.total_valor or 0)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Fechamento do Orçamento:")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    c.drawString(
        margin_x,
        y,
        "Total em Peso Bruto: " + _br_number(total_peso, 3, " kg"),
    )
    y -= 0.4 * cm

    c.drawString(
        margin_x,
        y,
        "Total em Valor: R$ " + _br_number(total_valor),
    )
    y -= 0.8 * cm

    c.setFont("Helvetica", 8)
    c.drawString(margin_x, y, "Documento gerado automaticamente pelo OrderSync.")

    c.showPage()
    c.save()

    with open(path, "rb") as f:
        return f.read()
