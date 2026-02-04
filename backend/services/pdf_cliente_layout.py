# backend/services/pdf_cliente_layout.py
"""
Layout simplificado do PDF para o cliente (Solicitação de orçamento)
Baseado no screenshot fornecido pelo usuário.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from pathlib import Path
import io

from models.pedido_pdf import PedidoPdf


def _br_number(value, decimals=2, suffix=""):
    """Formata número no padrão brasileiro."""
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


def gerar_pdf_cliente_simplificado(pedido: PedidoPdf) -> bytes:
    """
    Gera PDF com layout simplificado para o cliente.
    Título: "Solicitação de orçamento"
    """
    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    margin_x = 1.5 * cm
    margin_y = 1.0 * cm
    y_cursor = height - margin_y
    
    # ==================== LOGO ====================
    base_dir = Path(__file__).resolve().parents[2]
    logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png"
    
    if logo_path.exists():
        try:
            img = ImageReader(str(logo_path))
            logo_w = 3.5 * cm
            iw, ih = img.getSize()
            logo_h = logo_w * ih / iw
            logo_x = width - margin_x - logo_w
            logo_y = y_cursor - logo_h
            c.drawImage(img, logo_x, logo_y, width=logo_w, height=logo_h)
        except:
            pass
    
    # ==================== TÍTULO ====================
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin_x, y_cursor - 0.5*cm, "Solicitação de orçamento")
    y_cursor -= 1.5*cm
    
    # ==================== INFORMAÇÕES DO PEDIDO ====================
    c.setFont("Helvetica", 10)
    
    # Data do pedido
    data_pedido_str = "---"
    if pedido.data_pedido:
        data_pedido_str = pedido.data_pedido.strftime("%d/%m/%Y %H:%M:%S")
    c.drawString(margin_x, y_cursor, f"Data do pedido: {data_pedido_str}")
    
    # Cliente
    c.drawString(margin_x, y_cursor - 0.5*cm, f"Cliente: {pedido.cliente or '---'}")
    
    # Validade (lado direito)
    validade_x = width / 2
    c.drawString(validade_x, y_cursor, f"Validade: {pedido.validade_tabela or 'Não se aplica'}")
    
    # Data de entrega (lado direito)
    data_entrega_str = "a combinar"
    if pedido.data_entrega_ou_retirada:
        data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
    c.drawString(validade_x, y_cursor - 0.5*cm, f"Data de entrega: {data_entrega_str}")
    
    y_cursor -= 1.5*cm
    
    # ==================== TABELA DE PRODUTOS ====================
    
    # Determinar título da coluna de valor baseado em usar_valor_com_frete
    if pedido.usar_valor_com_frete:
        header_valor = "Valor c/ Frete"
    else:
        header_valor = "Valor s/ Frete"
    
    # Cabeçalho da tabela
    table_data = [[
        "Código",
        "Produto",
        "Embal.",
        "Qtd",
        header_valor,
        "Condição de Pagamento",
        "Markup %",
        "Valor C Markup"
    ]]
    
    # Linhas de produtos
    for item in pedido.itens:
        # Escolher valor correto baseado em usar_valor_com_frete
        if pedido.usar_valor_com_frete:
            valor_unitario = item.valor_entrega
        else:
            valor_unitario = item.valor_retira
        
        # Markup
        markup_display = "-"
        if item.markup and item.markup > 0:
            markup_display = f"{_br_number(item.markup, 2)}%"
        
        # Valor com markup
        valor_markup_display = "-"
        if item.valor_final_markup and item.valor_final_markup > 0:
            valor_markup_display = f"R$ {_br_number(item.valor_final_markup, 2)}"
        
        table_data.append([
            item.codigo or "",
            item.produto or "",
            item.embalagem or "",
            str(int(item.quantidade)) if item.quantidade else "0",
            f"R$ {_br_number(valor_unitario, 2)}",
            item.condicao_pagamento or "",
            markup_display,
            valor_markup_display
        ])
    
    # Criar tabela
    col_widths = [2.5*cm, 7*cm, 1.5*cm, 1.5*cm, 2.5*cm, 4*cm, 2*cm, 2.5*cm]
    
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.78, 0.70, 0.60)),  # Cor bege/marrom
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Qtd centralizada
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Valor à direita
        ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Markup % centralizado
        ('ALIGN', (7, 1), (7, -1), 'RIGHT'),   # Valor Markup à direita
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    
    # Desenhar tabela
    table_width, table_height = table.wrap(width - 2*margin_x, height)
    table.drawOn(c, margin_x, y_cursor - table_height)
    y_cursor -= table_height + 1*cm
    
    # ==================== RODAPÉ: TOTAIS E OBSERVAÇÕES ====================
    
    # Criar tabela de totais (lado esquerdo)
    totais_data = [
        ["Total em Peso Bruto", f"{_br_number(pedido.total_peso_bruto, 0)} kg"],
        ["Total em Valor", f"R$ {_br_number(pedido.total_valor, 2)}"]
    ]
    
    totais_table = Table(totais_data, colWidths=[5*cm, 3*cm])
    totais_table.setStyle(TableStyle([
        # Cabeçalho (primeira coluna)
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.78, 0.70, 0.60)),  # Cor bege/marrom
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        
        # Valores (segunda coluna)
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        
        # Bordas e padding
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    # Desenhar tabela de totais
    totais_width, totais_height = totais_table.wrap(8*cm, height)
    totais_table.drawOn(c, margin_x, y_cursor - totais_height)
    
    # Observações (lado direito, mais próximo)
    obs_x = margin_x + 10*cm  # Ajustado para ficar mais próximo
    obs_y = y_cursor
    
    # Título com fundo colorido
    c.setFillColor(colors.Color(0.78, 0.70, 0.60))  # Cor bege/marrom
    c.rect(obs_x, obs_y, width - obs_x - margin_x, 0.6*cm, fill=1, stroke=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(obs_x + 0.3*cm, obs_y + 0.15*cm, "Observações do Cliente:")
    
    # Desenhar caixa de observações
    obs_box_width = width - obs_x - margin_x
    obs_box_height = totais_height - 0.6*cm  # Mesma altura da tabela de totais
    c.setStrokeColor(colors.grey)
    c.setFillColor(colors.white)
    c.rect(obs_x, obs_y - obs_box_height - 0.6*cm, obs_box_width, obs_box_height, fill=1, stroke=1)
    
    # Texto das observações
    if pedido.observacoes:
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        # Quebrar texto em linhas
        obs_text = pedido.observacoes[:500]  # Limitar tamanho
        text_obj = c.beginText(obs_x + 0.3*cm, obs_y - 1.0*cm)
        text_obj.setFont("Helvetica", 9)
        
        # Quebrar em linhas de ~60 caracteres
        words = obs_text.split()
        line = ""
        for word in words:
            if len(line + word) < 60:
                line += word + " "
            else:
                text_obj.textLine(line.strip())
                line = word + " "
        if line:
            text_obj.textLine(line.strip())
        
        c.drawText(text_obj)
    else:
        c.setFillColor(colors.grey)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(obs_x + 0.3*cm, obs_y - 1.0*cm, "Digite aqui...")
    
    # Finalizar
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
