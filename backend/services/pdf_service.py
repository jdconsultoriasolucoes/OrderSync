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
from models.pedido_pdf import PedidoPdf

# cores da Supra
SUPRA_RED = colors.HexColor("#B3001F")
SUPRA_DARK = colors.black


def _br_number(valor: float, casas: int = 2, sufixo: str = "") -> str:
    txt = f"{valor:,.{casas}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return txt + sufixo


def _desenhar_pdf(pedido: PedidoPdf, path: str) -> None:
    """Desenha o PDF no arquivo `path` usando o layout bonitinho."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin_x = 2 * cm
    margin_y = 2 * cm
    y = height - margin_y

    # ==== LOGO + BARRA SUPERIOR ====
    base_dir = Path(__file__).resolve().parents[2]
    logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo.png"
    if not logo_path.exists():
        logo_env = os.getenv("ORDERSYNC_LOGO_PATH")
        if logo_env and Path(logo_env).exists():
            logo_path = Path(logo_env)
        else:
            logo_path = None

    barra_altura = 1.2 * cm
    c.setFillColor(SUPRA_RED)
    c.rect(0, y - barra_altura + 0.2 * cm, width, barra_altura, fill=1, stroke=0)

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
            # se der pau no logo, ignora e segue
            pass

    # título
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "DIGITAÇÃO DO ORÇAMENTO")

    # data
    c.setFont("Helvetica", 10)
    data_pedido = pedido.data_pedido
    if isinstance(data_pedido, datetime):
        data_str = data_pedido.strftime("%d/%m/%Y")
    elif data_pedido:
        data_str = data_pedido.strftime("%d/%m/%Y")
    else:
        data_str = ""
    c.drawRightString(width - margin_x, y - 0.1 * cm, data_str)

    c.setFillColor(SUPRA_DARK)
    y -= 1.6 * cm

    # ==== CÓDIGO / CLIENTE ====
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

    # ==== FRETE / DATA ENTREGA ou RETIRA ====
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
        1.8 * cm,
        5.0 * cm,
        2.0 * cm,
        1.5 * cm,
        2.7 * cm,
        2.7 * cm,
        2.0 * cm,
        2.0 * cm,
    ]

    from reportlab.platypus import Table

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
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


def gerar_pdf_pedido(*args, destino_dir: str = "/tmp", **kwargs):
    """
    Função compatível com os dois jeitos de uso:

    1) JEITO ANTIGO (código que está no Render agora):
        pedido_pdf = carregar_pedido_pdf(...)
        path_pdf = gerar_pdf_pedido(pedido_pdf)
        # retorna STRING com o caminho do arquivo

    2) JEITO NOVO (que você tem local):
        pdf_bytes = gerar_pdf_pedido(db, pedido_id)
        # retorna BYTES para anexar no e-mail
    """
    # --- destino_dir pode vir em kwargs ---
    if "destino_dir" in kwargs and kwargs["destino_dir"]:
        destino_dir = kwargs["destino_dir"]

    # Caso 1: chamado como gerar_pdf_pedido(pedido_pdf)
    if len(args) == 1 and isinstance(args[0], PedidoPdf):
        pedido = args[0]
        os.makedirs(destino_dir, exist_ok=True)
        path = os.path.join(destino_dir, f"pedido_{pedido.id_pedido}.pdf")
        _desenhar_pdf(pedido, path)
        return path

    # Caso 2: chamado como gerar_pdf_pedido(db, pedido_id) ou via kwargs
    if len(args) >= 2:
        db = args[0]
        pedido_id = args[1]
    elif "db" in kwargs and "pedido_id" in kwargs:
        db = kwargs["db"]
        pedido_id = kwargs["pedido_id"]
    else:
        raise TypeError("Uso inválido de gerar_pdf_pedido")

    # carrega os dados a partir do banco e gera o PDF
    pedido = carregar_pedido_pdf(db, int(pedido_id))
    os.makedirs(destino_dir, exist_ok=True)
    path = os.path.join(destino_dir, f"pedido_{pedido.id_pedido}.pdf")
    _desenhar_pdf(pedido, path)

    # aqui retornamos BYTES (uso novo)
    with open(path, "rb") as f:
        return f.read()
