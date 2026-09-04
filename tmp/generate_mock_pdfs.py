import sys
import io
import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Adiciona o diretório backend ao sys.path para podermos importar utils (se necessário)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Mock colors matching the system
SUPRA_BAR = colors.Color(0.78, 0.70, 0.60)
SUPRA_TEXT = colors.Color(0.1, 0.1, 0.1)
SUPRA_BG_LIGHT = colors.Color(0.95, 0.95, 0.95)

def _draw_header(c, width, height, title, subtitle=""):
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm
    available_width = width - 2 * margin_x
    top_y = height - margin_y

    # Header Bar
    faixa_h = 1.0 * cm
    faixa_y = top_y - 0.2 * cm
    c.setFillColor(SUPRA_BAR)
    c.rect(margin_x, faixa_y - faixa_h, available_width, faixa_h, stroke=0, fill=1)

    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x + 0.3 * cm, faixa_y - faixa_h + 0.3 * cm, title.upper())

    # Subtitle / Date
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin_x - 0.2*cm, faixa_y - faixa_h + 0.55 * cm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if subtitle:
        c.drawRightString(width - margin_x - 0.2*cm, faixa_y - faixa_h + 0.15 * cm, subtitle)

    return faixa_y - faixa_h - 0.5 * cm

def generate_mock_entrega_pdf():
    file_path = os.path.abspath(r"e:\OrderSync\tmp\mock_entrega.pdf")
    pagesize = A4
    c = canvas.Canvas(file_path, pagesize=pagesize)
    width, height = pagesize
    
    y = _draw_header(c, width, height, "Rota de Entrega - Em Bloco", "Data: 04/09/2026 | Veículo: Caminhão Baú - ABC-1234")
    
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.fontSize = 8
    
    # Mock Pedido 1
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(SUPRA_TEXT)
    c.drawString(1.0*cm, y, "[Pedido #1045] - Cliente: Supermercado Central LTDA")
    y -= 0.5*cm
    c.setFont("Helvetica", 8)
    c.drawString(1.0*cm, y, "Endereço: Rua das Flores, 123 - Centro, São Paulo/SP - CEP: 01000-000")
    y -= 0.4*cm
    c.drawString(1.0*cm, y, "Contato: (11) 99999-1111 - Falar com Marcos")
    y -= 0.5*cm
    
    data = [
        ["Cód", "Produto", "Qtd", "Unid", "Observações"],
        ["001", "Arroz Agulhinha 5kg", "50", "pct", ""],
        ["005", "Feijão Carioca 1kg", "100", "pct", "Cuidado frágil"]
    ]
    t = Table(data, colWidths=[1.5*cm, 7*cm, 2*cm, 1.5*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    tw, th = t.wrap(width, height)
    t.drawOn(c, 1.0*cm, y - th)
    y -= (th + 0.5*cm)
    
    c.setFont("Helvetica", 8)
    c.drawString(1.0*cm, y, "Assinatura do Recebedor: _____________________________________   Data/Hora: ___/___/___ às ___:___")
    y -= 1.5*cm
    
    # Mock Pedido 2
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(SUPRA_TEXT)
    c.drawString(1.0*cm, y, "[Pedido #1046] - Cliente: Padaria Pão Quente")
    y -= 0.5*cm
    c.setFont("Helvetica", 8)
    c.drawString(1.0*cm, y, "Endereço: Av. Paulista, 1500 - Bela Vista, São Paulo/SP - CEP: 01310-100")
    y -= 0.4*cm
    c.drawString(1.0*cm, y, "Contato: (11) 98888-2222 - Falar com Ana")
    y -= 0.5*cm
    
    data2 = [
        ["Cód", "Produto", "Qtd", "Unid", "Observações"],
        ["012", "Farinha de Trigo 25kg", "10", "sc", "Entregar pelos fundos"],
        ["015", "Óleo de Soja 900ml", "30", "cx", ""]
    ]
    t2 = Table(data2, colWidths=[1.5*cm, 7*cm, 2*cm, 1.5*cm, 7*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    tw, th = t2.wrap(width, height)
    t2.drawOn(c, 1.0*cm, y - th)
    y -= (th + 0.5*cm)
    
    c.setFont("Helvetica", 8)
    c.drawString(1.0*cm, y, "Assinatura do Recebedor: _____________________________________   Data/Hora: ___/___/___ às ___:___")
    y -= 1.0*cm
    
    c.showPage()
    c.save()
    return file_path

def generate_mock_resumo_pdf():
    file_path = os.path.abspath(r"e:\OrderSync\tmp\mock_resumo.pdf")
    pagesize = A4
    c = canvas.Canvas(file_path, pagesize=pagesize)
    width, height = pagesize
    
    y = _draw_header(c, width, height, "Resumo de Carregamento / Separação", "Data: 04/09/2026 | Total Pedidos: 2")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.0*cm, y, "Veículo: Caminhão Baú - ABC-1234 | Motorista: João Silva")
    y -= 0.8*cm
    
    data = [
        ["Cód", "Descrição do Produto", "Qtd Total", "Unid", "Conferido"],
        ["001", "Arroz Agulhinha 5kg", "50", "pct", "[    ]"],
        ["005", "Feijão Carioca 1kg", "100", "pct", "[    ]"],
        ["012", "Farinha de Trigo 25kg", "10", "sc", "[    ]"],
        ["015", "Óleo de Soja 900ml", "30", "cx", "[    ]"]
    ]
    t = Table(data, colWidths=[2*cm, 10*cm, 2.5*cm, 1.5*cm, 3*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('ALIGN', (4,0), (4,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    tw, th = t.wrap(width, height)
    t.drawOn(c, 1.0*cm, y - th)
    y -= (th + 1.0*cm)
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.0*cm, y, "Observações de Carregamento: Revisar validade da Farinha.")
    y -= 1.5*cm
    c.setFont("Helvetica", 9)
    c.drawString(1.0*cm, y, "Assinatura do Conferente (Estoque): _____________________________________________")
    y -= 1.0*cm
    c.drawString(1.0*cm, y, "Assinatura do Motorista (Aceite da Carga): ________________________________________")
    
    c.showPage()
    c.save()
    return file_path

def generate_mock_retirada_pdf():
    file_path = os.path.abspath(r"e:\OrderSync\tmp\mock_retirada.pdf")
    pagesize = A4
    c = canvas.Canvas(file_path, pagesize=pagesize)
    width, height = pagesize
    
    y = _draw_header(c, width, height, "Ordem de Retirada", "Data Agendada: 04/09/2026")
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(SUPRA_TEXT)
    c.drawString(1.0*cm, y, "[Pedido #2099] - Cliente/Fornecedor: Distribuidora Atacadão S/A")
    y -= 0.5*cm
    c.setFont("Helvetica", 8)
    c.drawString(1.0*cm, y, "Endereço Cadastral: Rua XV de Novembro, 800 - Centro, São Paulo/SP - CEP: 01010-000")
    y -= 0.4*cm
    c.drawString(1.0*cm, y, "Contato: (11) 97777-3333 - Falar com Roberto")
    y -= 0.8*cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.0*cm, y, "DADOS DO VEÍCULO PARA RETIRADA:")
    y -= 0.4*cm
    c.setFont("Helvetica", 9)
    c.drawString(1.0*cm, y, "Motorista Autorizado: Carlos Mendes")
    y -= 0.4*cm
    c.drawString(1.0*cm, y, "Placa do Veículo: XYZ-9876")
    y -= 0.8*cm
    
    data = [
        ["Cód", "Descrição do Produto", "Qtd a Retirar", "Unid", "Conferido"],
        ["022", "Açúcar Refinado 1kg", "200", "pct", "[    ]"],
        ["030", "Café Torrado 500g", "50", "cx", "[    ]"]
    ]
    t = Table(data, colWidths=[2*cm, 10*cm, 2.5*cm, 1.5*cm, 3*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('ALIGN', (4,0), (4,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    tw, th = t.wrap(width, height)
    t.drawOn(c, 1.0*cm, y - th)
    y -= (th + 1.0*cm)
    
    c.setFont("Helvetica", 9)
    c.drawString(1.0*cm, y, "Assinatura de quem Separou: _____________________________________________")
    y -= 1.0*cm
    c.drawString(1.0*cm, y, "Assinatura de quem Retirou (Carlos Mendes): ________________________________________")
    y -= 1.0*cm
    c.drawString(1.0*cm, y, "Data/Hora da Saída: ___/___/___ às ___:___")
    
    c.showPage()
    c.save()
    return file_path

if __name__ == "__main__":
    generate_mock_entrega_pdf()
    generate_mock_resumo_pdf()
    generate_mock_retirada_pdf()
    print("Mock PDFs generated in e:\\OrderSync\\tmp\\")
