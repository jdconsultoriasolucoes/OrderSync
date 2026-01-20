#!/usr/bin/env python3
"""
Script ALTERNATIVO para converter Manual Markdown para PDF
Usa reportlab (mais compatível no Windows, não requer GTK+)
"""

import os
import sys
from pathlib import Path
import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

def markdown_to_elements(md_file_path, images_dir='imagens'):
    """
    Converte Markdown para elementos do ReportLab.
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Converter Markdown para HTML primeiro
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'tables'])
    html = md.convert(md_content)
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Criar estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        keepWithNext=True
    )
    
    heading1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=20,
        spaceBefore=30,
        keepWithNext=True
    )
    
    heading2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#555'),
        spaceAfter=15,
        spaceBefore=20,
        keepWithNext=True
    )
    
    heading3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#666'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )
    
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        backColor=colors.HexColor('#f4f4f4'),
        leftIndent=10,
        rightIndent=10
    )
    
    elements = []
    
    # Processar linhas do Markdown diretamente (mais simples)
    lines = md_content.split('\n')
    in_code_block = False
    code_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Ignorar linhas vazias no início
        if not line_stripped and not elements:
            continue
        
        # Processar código
        if line_stripped.startswith('```'):
            if in_code_block:
                # Fechar bloco de código
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    elements.append(Paragraph(f'<font face="Courier" size="9">{code_text}</font>', code_style))
                    code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_lines.append(line)
            continue
        
        # Títulos
        if line_stripped.startswith('# '):
            text = line_stripped[2:].strip()
            elements.append(Paragraph(text, title_style))
            elements.append(Spacer(1, 0.5*cm))
        elif line_stripped.startswith('## '):
            text = line_stripped[3:].strip()
            elements.append(PageBreak() if len(elements) > 10 else Spacer(1, 0.3*cm))
            elements.append(Paragraph(text, heading1_style))
            elements.append(Spacer(1, 0.3*cm))
        elif line_stripped.startswith('### '):
            text = line_stripped[4:].strip()
            elements.append(Paragraph(text, heading2_style))
            elements.append(Spacer(1, 0.2*cm))
        elif line_stripped.startswith('#### '):
            text = line_stripped[5:].strip()
            elements.append(Paragraph(text, heading3_style))
            elements.append(Spacer(1, 0.15*cm))
        
        # Imagens
        elif line_stripped.startswith('![') and '](' in line_stripped:
            try:
                # Extrair caminho da imagem
                start = line_stripped.find('](') + 2
                end = line_stripped.find(')', start)
                img_path = line_stripped[start:end]
                
                # Extrair legenda
                caption_start = line_stripped.find('[') + 1
                caption_end = line_stripped.find(']', caption_start)
                caption = line_stripped[caption_start:caption_end] if caption_start > 0 else ""
                
                # Caminho completo da imagem
                full_img_path = os.path.join(os.path.dirname(md_file_path), img_path)
                
                if os.path.exists(full_img_path):
                    try:
                        # Adicionar imagem
                        img = Image(full_img_path, width=15*cm, height=10*cm, kind='proportional')
                        elements.append(Spacer(1, 0.3*cm))
                        elements.append(img)
                        
                        # Adicionar legenda
                        if caption:
                            caption_style = ParagraphStyle(
                                'Caption',
                                parent=styles['Normal'],
                                fontSize=9,
                                textColor=colors.HexColor('#666'),
                                alignment=TA_CENTER,
                                fontStyle='italic'
                            )
                            elements.append(Spacer(1, 0.1*cm))
                            elements.append(Paragraph(caption, caption_style))
                        elements.append(Spacer(1, 0.3*cm))
                    except Exception as e:
                        # Erro ao carregar imagem - adicionar aviso
                        aviso_style = ParagraphStyle(
                            'AvisoImagem',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.HexColor('#d32f2f'),
                            alignment=TA_CENTER,
                            fontStyle='italic',
                            backColor=colors.HexColor('#ffebee')
                        )
                        elements.append(Spacer(1, 0.2*cm))
                        elements.append(Paragraph(
                            f'⚠️ [Imagem não pôde ser carregada: {os.path.basename(img_path)}]',
                            aviso_style
                        ))
                        elements.append(Spacer(1, 0.2*cm))
                else:
                    # Imagem não encontrada - adicionar aviso visual
                    aviso_style = ParagraphStyle(
                        'AvisoImagem',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.HexColor('#d32f2f'),
                        alignment=TA_CENTER,
                        fontStyle='italic',
                        backColor=colors.HexColor('#ffebee')
                    )
                    elements.append(Spacer(1, 0.2*cm))
                    elements.append(Paragraph(
                        f'📷 [Imagem não encontrada: {os.path.basename(img_path)}]<br/>'
                        f'<font size="8">Execute "python verificar_imagens.py" para ver quais imagens faltam</font>',
                        aviso_style
                    ))
                    elements.append(Spacer(1, 0.2*cm))
            except Exception as e:
                print(f"⚠️  Erro ao processar imagem: {e}")
        
        # Listas
        elif line_stripped.startswith('- ') or line_stripped.startswith('* '):
            text = line_stripped[2:].strip()
            # Formatar como lista
            bullet_text = f"• {text}"
            elements.append(Paragraph(bullet_text, normal_style))
        
        # Texto normal
        elif line_stripped and not line_stripped.startswith('**') and not line_stripped.startswith('---'):
            # Processar formatação básica
            text = line
            # Converter **texto** para <b>texto</b>
            import re
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'`(.+?)`', r'<font face="Courier" size="9">\1</font>', text)
            
            if text.strip():
                elements.append(Paragraph(text, normal_style))
        
        # Separador
        elif line_stripped.startswith('---'):
            elements.append(Spacer(1, 0.5*cm))
    
    return elements

def convert_md_to_pdf_reportlab(md_file_path, output_pdf_path, images_dir='imagens'):
    """
    Converte Markdown para PDF usando ReportLab.
    """
    print(f"📖 Lendo arquivo: {md_file_path}")
    
    if not os.path.exists(md_file_path):
        print(f"❌ Erro: Arquivo não encontrado: {md_file_path}")
        return False
    
    try:
        print("🔄 Processando Markdown...")
        elements = markdown_to_elements(md_file_path, images_dir)
        
        print("🔄 Gerando PDF...")
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm
        )
        
        # Construir PDF
        doc.build(elements)
        
        print(f"✅ PDF gerado com sucesso: {output_pdf_path}")
        print(f"📄 Tamanho do arquivo: {os.path.getsize(output_pdf_path) / 1024:.2f} KB")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Função principal.
    """
    md_file = "MANUAL_USUARIO_ORDERSYNC.md"
    output_pdf = "MANUAL_USUARIO_ORDERSYNC.pdf"
    images_dir = "imagens"
    
    print("=" * 60)
    print("📚 Gerador de PDF - Manual do Usuário OrderSync")
    print("   (Usando ReportLab - Compatível com Windows)")
    print("=" * 60)
    print()
    
    if not os.path.exists(md_file):
        print(f"❌ Erro: Arquivo não encontrado: {md_file}")
        return
    
    success = convert_md_to_pdf_reportlab(md_file, output_pdf, images_dir)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Conversão concluída!")
        print(f"📄 Arquivo gerado: {output_pdf}")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ Falha na conversão.")
        print("=" * 60)

if __name__ == "__main__":
    main()
