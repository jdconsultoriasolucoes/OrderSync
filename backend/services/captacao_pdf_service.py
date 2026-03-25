import io
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def hex_to_color(hex_str: str):
    """Converte hexadecimal para cor do reportlab."""
    hex_str = hex_str.lstrip('#')
    return colors.Color(*[int(hex_str[i:i+2], 16)/255 for i in (0, 2, 4)])

def gerar_pdf_prospeccao(dados_captacao: list, nome_vendedor: str) -> bytes:
    """
    Gera um PDF em formato paisagem com a lista de clientes para prospecção do vendedor.
    Colunas: Rota Geral, Rota Aprox, Vendedor, Cód, Cliente, Nome Fantasia, Município, Última Compra, Período, Previsão e Status.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
        title=f"Relatório de Prospecção - {nome_vendedor}"
    )

    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo do Título
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1, # Centralizado
        spaceAfter=20
    )
    
    hoje_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Relatório de Prospecção - {nome_vendedor}", title_style))
    elements.append(Paragraph(f"Gerado em: {hoje_str}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # Cabeçalho da Tabela
    headers = [
        "Rota Geral", 
        "Rota Aprox.", 
        "Vendedor", 
        "Cód.", 
        "Cliente", 
        "Nome Fantasia", 
        "Município", 
        "Última\nCompra", 
        "Período\n(Dias)", 
        "Previsão\nPróxima", 
        "Status"
    ]

    # Convertendo os dados para a tabela
    data = [headers]
    
    # Cores de background para as linhas
    row_colors = []
    
    # Estilos customizados para células
    style_normal = styles["Normal"]
    style_normal.fontSize = 7
    style_normal.leading = 8
    
    style_bold = ParagraphStyle('BoldSmall', fontName='Helvetica-Bold', fontSize=7, leading=8)

    for item in dados_captacao:
        # Pega a cor baseada no status
        status_cor = item.get("status_cor", "cinza")
        cor_hex = "#f3f4f6" # Cinza default
        if status_cor == "verde":
            cor_hex = "#dcfce7"
        elif status_cor == "amarelo":
            cor_hex = "#fef3c7"
        elif status_cor == "vermelho":
            cor_hex = "#fee2e2"
            
        row_colors.append(hex_to_color(cor_hex))
        
        status_label = "Ativo" if item.get("ativo", False) else "Inativo"
        
        row = [
            Paragraph(str(item.get("rota_geral") or "-"), style_normal),
            Paragraph(str(item.get("rota_aproximacao") or "-"), style_normal),
            Paragraph(str(item.get("vendedor") or "-"), style_normal),
            Paragraph(str(item.get("codigo_cliente") or "-"), style_bold),
            Paragraph(str(item.get("cliente") or "-"), style_normal),
            Paragraph(str(item.get("nome_fantasia") or "-"), style_normal),
            Paragraph(str(item.get("municipio") or "-"), style_normal),
            str(item.get("data_ultima_compra") or "-"),
            str(item.get("periodo_em_dias") or "-"),
            str(item.get("data_previsao_proxima") or "-"),
            status_label
        ]
        data.append(row)

    # Configuração da Tabela
    # A4 Landscape width é 842. Margens são 40 (20L + 20R). Available width = 802
    col_widths = [65, 65, 60, 40, 130, 130, 100, 50, 45, 55, 40]
    
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Estilo base da tabela
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")), # Header dark
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        # Alinhamentos específicos
        ('ALIGN', (3, 0), (3, -1), 'CENTER'), # Cód
        ('ALIGN', (7, 0), (9, -1), 'CENTER'), # Datas e Período
        ('ALIGN', (10, 0), (10, -1), 'CENTER'), # Status
    ])
    
    # Aplica as cores nas linhas de dados
    for i, color in enumerate(row_colors, start=1):
        table_style.add('BACKGROUND', (0, i), (-1, i), color)
        
    t.setStyle(table_style)
    elements.append(t)

    doc.build(elements)
    
    return buffer.getvalue()
