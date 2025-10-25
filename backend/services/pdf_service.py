# services/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
import os

def gerar_pdf_pedido(pedido, itens, cliente, destino_dir="/tmp") -> str:
    """
    Gera um PDF simples do pedido e retorna o caminho do arquivo.
    """
    os.makedirs(destino_dir, exist_ok=True)
    filename = f"pedido_{pedido.id}.pdf"
    path = os.path.join(destino_dir, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    y = height - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, f"Pedido #{pedido.id} - CONFIRMADO")
    y -= 0.7*cm

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Cliente: {getattr(cliente, 'nome', '---')}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 0.5*cm

    # Itens
    y -= 0.3*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Itens")
    y -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, "Produto")
    c.drawString(9*cm, y, "Qtd")
    c.drawString(11*cm, y, "Unit")
    c.drawString(14*cm, y, "Total")
    y -= 0.4*cm
    c.line(2*cm, y, 19*cm, y)
    y -= 0.4*cm

    total_geral = 0
    for it in itens:
        # ajuste para os nomes reais dos campos do seu modelo
        prod = getattr(it, "descricao", getattr(it, "produto_nome", str(getattr(it, "produto_id", ""))))
        qtd = float(getattr(it, "quantidade", 0) or 0)
        unit = float(getattr(it, "preco_unit", 0) or 0)
        total = qtd * unit
        total_geral += total

        c.drawString(2*cm, y, str(prod)[:60])
        c.drawRightString(10.5*cm, y, f"{qtd:g}")
        c.drawRightString(13.5*cm, y, f"{unit:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
        c.drawRightString(19*cm, y, f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
        y -= 0.5*cm
        if y < 3*cm:
            c.showPage()
            y = height - 2*cm

    # Totais
    if y < 4*cm:
        c.showPage()
        y = height - 2*cm

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(19*cm, y, f"Total: R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
    y -= 0.7*cm

    c.setFont("Helvetica", 8)
    c.drawString(2*cm, y, "Documento gerado automaticamente pelo OrderSync.")

    c.showPage()
    c.save()
    return path
