#!/usr/bin/env python3
"""
Script para converter o Manual do Usuário Markdown para PDF
Inclui suporte para imagens e formatação completa.
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def markdown_to_html(md_file_path, images_dir='imagens'):
    """
    Converte arquivo Markdown para HTML, processando imagens.
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Configurar extensões do Markdown
    md = markdown.Markdown(extensions=[
        'extra',
        'codehilite',
        'tables',
        'toc',
        'fenced_code'
    ])
    
    # Converter Markdown para HTML
    html_body = md.convert(md_content)
    
    # Criar HTML completo com estilos
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @top-center {{
                    content: "Manual do Usuário - OrderSync";
                    font-size: 10pt;
                    color: #666;
                }}
                @bottom-center {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 10pt;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                page-break-after: avoid;
            }}
            
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 5px;
                margin-top: 30px;
                page-break-after: avoid;
            }}
            
            h3 {{
                color: #555;
                margin-top: 25px;
                page-break-after: avoid;
            }}
            
            h4 {{
                color: #666;
                margin-top: 20px;
            }}
            
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                border: 1px solid #ddd;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                page-break-inside: avoid;
            }}
            
            .figure-caption {{
                text-align: center;
                font-style: italic;
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
                margin-bottom: 20px;
            }}
            
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            
            ul, ol {{
                margin-left: 20px;
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 8px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                page-break-inside: avoid;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            
            th {{
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 20px 0;
                padding-left: 20px;
                color: #555;
                font-style: italic;
            }}
            
            strong {{
                color: #2c3e50;
                font-weight: bold;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 30px 0;
            }}
            
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
            
            .toc {{
                background-color: #f8f9fa;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                page-break-inside: avoid;
            }}
            
            .toc ul {{
                list-style-type: none;
                margin-left: 0;
            }}
            
            .toc li {{
                margin-bottom: 5px;
            }}
            
            .toc a {{
                color: #2c3e50;
            }}
            
            @media print {{
                body {{
                    font-size: 11pt;
                }}
                h1 {{
                    font-size: 24pt;
                }}
                h2 {{
                    font-size: 18pt;
                }}
                h3 {{
                    font-size: 14pt;
                }}
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    return html_template

def convert_md_to_pdf(md_file_path, output_pdf_path, images_dir='imagens'):
    """
    Converte arquivo Markdown para PDF.
    """
    print(f"📖 Lendo arquivo: {md_file_path}")
    
    if not os.path.exists(md_file_path):
        print(f"❌ Erro: Arquivo não encontrado: {md_file_path}")
        return False
    
    try:
        # Converter Markdown para HTML
        print("🔄 Convertendo Markdown para HTML...")
        html_content = markdown_to_html(md_file_path, images_dir)
        
        # Verificar se pasta de imagens existe
        if os.path.exists(images_dir):
            print(f"✅ Pasta de imagens encontrada: {images_dir}")
        else:
            print(f"⚠️  Aviso: Pasta de imagens não encontrada: {images_dir}")
            print("   As imagens não serão incluídas no PDF.")
        
        # Converter HTML para PDF
        print("🔄 Gerando PDF...")
        base_url = Path(md_file_path).parent.absolute()
        
        HTML(string=html_content, base_url=str(base_url)).write_pdf(
            output_pdf_path,
            stylesheets=None  # Estilos já estão no HTML
        )
        
        print(f"✅ PDF gerado com sucesso: {output_pdf_path}")
        print(f"📄 Tamanho do arquivo: {os.path.getsize(output_pdf_path) / 1024:.2f} KB")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {str(e)}")
        print("\n💡 Dicas:")
        print("   1. Certifique-se de que as bibliotecas estão instaladas:")
        print("      pip install markdown weasyprint")
        print("   2. No Windows, pode ser necessário instalar GTK+ para WeasyPrint")
        print("   3. Alternativa: use o script alternativo com reportlab")
        return False

def main():
    """
    Função principal.
    """
    # Arquivos
    md_file = "MANUAL_USUARIO_ORDERSYNC.md"
    output_pdf = "MANUAL_USUARIO_ORDERSYNC.pdf"
    images_dir = "imagens"
    
    print("=" * 60)
    print("📚 Gerador de PDF - Manual do Usuário OrderSync")
    print("=" * 60)
    print()
    
    # Verificar se arquivo existe
    if not os.path.exists(md_file):
        print(f"❌ Erro: Arquivo não encontrado: {md_file}")
        print("   Certifique-se de estar na pasta correta.")
        return
    
    # Converter
    success = convert_md_to_pdf(md_file, output_pdf, images_dir)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Conversão concluída!")
        print(f"📄 Arquivo gerado: {output_pdf}")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ Falha na conversão. Veja as dicas acima.")
        print("=" * 60)

if __name__ == "__main__":
    main()
