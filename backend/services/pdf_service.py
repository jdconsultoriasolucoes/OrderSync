# services/pdf_service.py

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os

def gerar_pdf_pedido(pedido_pdf, destino_dir="/tmp"):
    """
    pedido_pdf = objeto PedidoPdf vindo do endpoint /dados_pdf
    """

    filename = f"pedido_{pedido_pdf.id_pedido}.pdf"
    path = os.path.join(destino_dir, filename)

    c = canvas.Canvas(path, pagesize=A4)

    # CABEÇALHO
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, 28*cm, "DIGITAÇÃO DO ORÇAMENTO")

    # Data
    c.setFont("Helvetica", 10)
    c.drawString(16*cm, 28*cm, pedido_pdf.data_pedido.strftime("%d/%m/%Y"))

    # Código + Cliente
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, 26.5*cm, f"Codigo: {pedido_pdf.codigo_cliente or '---'}")
    c.drawString(7*cm, 26.5*cm, f"Cliente: {pedido_pdf.cliente}")

    # Valor Frete
    c.drawString(2*cm, 25.5*cm, f"Valor Frete (TO): R$ {pedido_pdf.frete_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Data de entrega
    if pedido_pdf.data_entrega_ou_retirada:
        c.drawString(
            12*cm, 25.5*cm,
            f"Data da Entrega/Retira: {pedido_pdf.data_entrega_ou_retirada.strftime('%d/%m/%Y')}"
        )

    # TÍTULOS DA TABELA
    y = 24*cm
    c.setFont("Helvetica-Bold", 9)
    headers = ["Codigo", "Produto", "Embalagem", "Qtd", "Cond. Pgto", "Comissão", "Retira", "Entrega"]
    x_positions = [2*cm, 4*cm, 9*cm, 12*cm, 14*cm, 16*cm, 18*cm, 19.5*cm]

    for h, x in zip(headers, x_positions):
        c.drawString(x, y, h)

    # ITENS
    c.setFont("Helvetica", 9)
    y -= 0.7*cm

    for item in pedido_pdf.itens:
        if y < 3*cm:  
            c.showPage()
            y = 27*cm

        c.drawString(2*cm, y, item.codigo)
        c.drawString(4*cm, y, item.produto[:30])
        c.drawString(9*cm, y, item.embalagem or "")
        c.drawString(12*cm, y, str(item.quantidade))
        c.drawString(14*cm, y, item.condicao_pagamento or "")
        c.drawString(16*cm, y, item.tabela_comissao or "")
        c.drawRightString(19*cm, y, f"{item.valor_retira:.2f}")
        c.drawRightString(21*cm, y, f"{item.valor_entrega:.2f}")
        y -= 0.6*cm

    # FECHAMENTO
    y -= 1*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Fechamento do Orçamento:")

    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Total em Peso Bruto: {pedido_pdf.total_peso_bruto:,.3f} kg".replace(",", "X").replace(".", ",").replace("X", "."))

    y -= 0.6*cm
    c.drawString(2*cm, y, f"Total em Valor: R$ {pedido_pdf.total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    c.showPage()
    c.save()

    return path
