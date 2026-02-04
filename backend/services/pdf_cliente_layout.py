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
    Formato: Retrato (A4)
    Suporta múltiplas páginas para muitos produtos.
    """
    buffer = io.BytesIO()
    pagesize = A4  # RETRATO (não mais landscape)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    margin_x = 1.5 * cm
    margin_y = 1.0 * cm
    
    # ==================== FUNÇÃO AUXILIAR: DESENHAR CABEÇALHO ====================
    def desenhar_cabecalho(y_start):
        """Desenha cabeçalho da página e retorna y_cursor após cabeçalho"""
        y = y_start
        
        # Logo
        base_dir = Path(__file__).resolve().parents[2]
        logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png"
        
        if logo_path.exists():
            try:
                img = ImageReader(str(logo_path))
                logo_w = 3.0 * cm
                iw, ih = img.getSize()
                logo_h = logo_w * ih / iw
                logo_x = width - margin_x - logo_w
                logo_y = y - logo_h
                c.drawImage(img, logo_x, logo_y, width=logo_w, height=logo_h)
            except:
                pass
        
        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_x, y - 0.5*cm, "Solicitação de orçamento")
        y -= 1.2*cm
        
        # Criar tabela com informações do pedido
        data_pedido_str = "---"
        if pedido.data_pedido:
            data_pedido_str = pedido.data_pedido.strftime("%d/%m/%Y %H:%M:%S")
        
        data_entrega_str = "a combinar"
        if pedido.data_entrega_ou_retirada:
            data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
        
        info_data = [
            ["Data do pedido:", data_pedido_str, "Validade:", pedido.validade_tabela or "Não se aplica"],
            ["Cliente:", pedido.cliente or "---", "Data de entrega:", data_entrega_str]
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 2.5*cm, 5.5*cm])
        info_table.setStyle(TableStyle([
            # Labels (colunas 0 e 2)
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            
            # Valores (colunas 1 e 3)
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            
            # Sem bordas
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        info_width, info_height = info_table.wrap(width - 2*margin_x, height)
        info_table.drawOn(c, margin_x, y - info_height)
        y -= info_height + 0.5*cm
        
        return y
    
    # ==================== PREPARAR DADOS DA TABELA ====================
    
    # Determinar título da coluna de valor
    if pedido.usar_valor_com_frete:
        header_valor = "Valor c/ Frete"
    else:
        header_valor = "Valor s/ Frete"
    
    # Cabeçalho da tabela
    table_header = [
        "Código",
        "Produto",
        "Embal.",
        "Qtd",
        header_valor,
        "Condição de\nPagamento",
        "Markup\n%",
        "Valor C\nMarkup"
    ]
    
    # Preparar todas as linhas de produtos
    all_rows = []
    for item in pedido.itens:
        # Escolher valor correto
        if pedido.usar_valor_com_frete:
            valor_unitario = item.valor_entrega
        else:
            valor_unitario = item.valor_retira
        
        # Markup - só mostrar se houver diferença real
        markup_display = "-"
        valor_markup_display = "-"
        
        # Verificar se há markup aplicado (valor final diferente do valor base)
        if item.valor_final_markup and item.valor_final_markup > 0:
            # Comparar com o valor que está sendo usado
            if abs(item.valor_final_markup - valor_unitario) > 0.01:  # Diferença maior que 1 centavo
                if item.markup and item.markup > 0:
                    markup_display = f"{_br_number(item.markup, 2)}%"
                valor_markup_display = f"R$ {_br_number(item.valor_final_markup, 2)}"
        
        all_rows.append([
            item.codigo or "",
            item.produto or "",
            item.embalagem or "",
            str(int(item.quantidade)) if item.quantidade else "0",
            f"R$ {_br_number(valor_unitario, 2)}",
            item.condicao_pagamento or "",
            markup_display,
            valor_markup_display
        ])
    
    # ==================== PAGINAÇÃO ====================
    
    # Larguras das colunas (ajustadas para retrato)
    col_widths = [1.8*cm, 5*cm, 1.2*cm, 1*cm, 2*cm, 3*cm, 1.3*cm, 2*cm]
    
    # Altura aproximada de cada linha
    row_height = 0.6*cm
    header_height = 0.8*cm
    
    # Espaço disponível para tabela na primeira página
    y_cursor = height - margin_y
    y_after_header = desenhar_cabecalho(y_cursor)
    space_first_page = y_after_header - margin_y - 4*cm  # Reservar espaço para totais
    
    # Espaço disponível em páginas subsequentes
    space_other_pages = height - 2*margin_y - 1*cm  # Margem + pequeno espaço
    
    # Calcular quantas linhas cabem por página
    rows_first_page = int((space_first_page - header_height) / row_height)
    rows_other_pages = int((space_other_pages - header_height) / row_height)
    
    # Dividir linhas em páginas
    page_rows = []
    if len(all_rows) <= rows_first_page:
        # Tudo cabe na primeira página
        page_rows.append(all_rows)
    else:
        # Primeira página
        page_rows.append(all_rows[:rows_first_page])
        remaining = all_rows[rows_first_page:]
        
        # Páginas subsequentes
        while remaining:
            page_rows.append(remaining[:rows_other_pages])
            remaining = remaining[rows_other_pages:]
    
    # ==================== DESENHAR PÁGINAS ====================
    
    for page_num, rows in enumerate(page_rows):
        is_first_page = (page_num == 0)
        is_last_page = (page_num == len(page_rows) - 1)
        
        if is_first_page:
            y_cursor = y_after_header
        else:
            # Nova página
            c.showPage()
            y_cursor = height - margin_y - 1*cm
        
        # Criar tabela para esta página
        table_data = [table_header] + rows
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.78, 0.70, 0.60)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Qtd
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Valor
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Markup %
            ('ALIGN', (7, 1), (7, -1), 'RIGHT'),   # Valor Markup
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))
        
        # Desenhar tabela
        table_width, table_height = table.wrap(width - 2*margin_x, height)
        table.drawOn(c, margin_x, y_cursor - table_height)
        y_cursor -= table_height + 0.5*cm
        
        # ==================== TOTAIS E OBSERVAÇÕES (APENAS NA ÚLTIMA PÁGINA) ====================
        
        if is_last_page:
            # Tabela de totais
            totais_data = [
                ["Total em Peso Bruto", f"{_br_number(pedido.total_peso_bruto, 0)} kg"],
                ["Total em Valor", f"R$ {_br_number(pedido.total_valor, 2)}"]
            ]
            
            totais_table = Table(totais_data, colWidths=[4*cm, 2.5*cm])
            totais_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.78, 0.70, 0.60)),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (1, 0), (1, -1), 9),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            totais_width, totais_height = totais_table.wrap(6.5*cm, height)
            totais_table.drawOn(c, margin_x, y_cursor - totais_height)
            
            # Observações (lado direito, PERFEITAMENTE alinhado com totais)
            obs_x = margin_x + 7.5*cm
            obs_y_top = y_cursor  # Topo alinhado com topo dos totais
            
            # Título com fundo colorido
            c.setFillColor(colors.Color(0.78, 0.70, 0.60))
            obs_title_height = 0.5*cm
            c.rect(obs_x, obs_y_top - obs_title_height, width - obs_x - margin_x, obs_title_height, fill=1, stroke=0)
            
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(obs_x + 0.2*cm, obs_y_top - obs_title_height + 0.15*cm, "Observações do Cliente:")
            
            # Caixa de observações (começa logo abaixo do título, alinha com base dos totais)
            obs_box_width = width - obs_x - margin_x
            obs_box_y_top = obs_y_top - obs_title_height
            obs_box_height = totais_height - obs_title_height
            
            c.setStrokeColor(colors.grey)
            c.setFillColor(colors.white)
            c.rect(obs_x, obs_box_y_top - obs_box_height, obs_box_width, obs_box_height, fill=1, stroke=1)
            
            # Texto das observações
            if pedido.observacoes:
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 8)
                text_obj = c.beginText(obs_x + 0.2*cm, obs_box_y_top - 0.3*cm)
                text_obj.setFont("Helvetica", 8)
                
                # Quebrar em linhas
                obs_text = pedido.observacoes[:400]
                words = obs_text.split()
                line = ""
                for word in words:
                    if len(line + word) < 50:
                        line += word + " "
                    else:
                        text_obj.textLine(line.strip())
                        line = word + " "
                if line:
                    text_obj.textLine(line.strip())
                
                c.drawText(text_obj)
            else:
                c.setFillColor(colors.grey)
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(obs_x + 0.2*cm, obs_box_y_top - 0.3*cm, "Digite aqui...")
    
    # Finalizar
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
