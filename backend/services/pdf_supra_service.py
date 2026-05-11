import io
import logging
from datetime import datetime
from pathlib import Path
import openpyxl

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from .excel_supra_service import gerar_excel_cliente_supra

logger = logging.getLogger("ordersync.pdf_supra")

# Assets
_BASE = Path(__file__).resolve().parent.parent / "assets"
_LOGO_PATH  = _BASE / "img_aba_Cadastro_Parte_1_0.png"
_QR_PATH    = _BASE / "img_aba_Cadastro_Parte_1_1.png"

def _s(val):
    return str(val) if val is not None else ""

def gerar_pdf_cliente_supra(cli) -> bytes:
    """
    Gera o PDF do Cadastro Supra baseado DIRETAMENTE no preenchimento do Excel (Aba 1).
    Isso garante que o layout seja idêntico ao Excel.
    """
    try:
        # 1. Gera o Excel preenchido para servir de base
        excel_bytes = gerar_excel_cliente_supra(cli)
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
        ws = wb["Cadastro Parte 1"]

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        mx = 0.5 * cm  # Margem lateral
        
        # 2. Constrói a matriz de dados lendo do Excel
        matrix = [["" for _ in range(11)] for _ in range(65)]
        for r in range(1, 64):
            for c_idx in range(1, 12):
                cell = ws.cell(row=r, column=c_idx)
                if cell.value:
                    matrix[r-1][c_idx-1] = _s(cell.value)

        # 3. Geometria (Points)
        # Larguras de colunas (Excel width units to cm approx)
        u = 0.142 * cm
        col_w_base = [9.71*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 12.14*u]
        total_w = sum(col_w_base)
        scale = (w - 2*mx) / total_w
        col_w = [cw * scale for cw in col_w_base]
        
        row_h = [13.5] * 65
        for i in range(7, 13): row_h[i] = 23.25 # Cabeçalho dados
        row_h[22] = 20 # Rota
        for i in [4, 18, 26, 30, 36, 42, 47, 53, 59]: row_h[i] = 4.0 # Spacers

        # 4. Spans (Lê os merges do Excel)
        spans = []
        for merged_range in ws.merged_cells.ranges:
            s_row, s_col, e_row, e_col = merged_range.bounds
            if s_row <= 64 and s_col <= 11:
                spans.append(('SPAN', (s_col-1, s_row-1), (min(e_col-1, 10), min(e_row-1, 64))))

        _HEADER_COLOR = colors.Color(128/255, 64/255, 0) # Marrom Supra
        
        style_list = spans + [
            ('GRID', (0,5), (10,63), 0.3, colors.grey),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 6.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            # Headers cores (Marrom Alisul)
            ('BACKGROUND', (0,5), (7,5), _HEADER_COLOR),
            ('BACKGROUND', (8,5), (10,5), _HEADER_COLOR),
            ('BACKGROUND', (0,13), (10,13), _HEADER_COLOR),
            ('BACKGROUND', (0,19), (10,19), _HEADER_COLOR),
            ('BACKGROUND', (0,27), (10,27), _HEADER_COLOR),
            ('BACKGROUND', (0,32), (10,32), _HEADER_COLOR),
            ('BACKGROUND', (0,37), (10,37), _HEADER_COLOR),
            ('BACKGROUND', (0,43), (10,43), _HEADER_COLOR),
            ('BACKGROUND', (0,48), (10,48), _HEADER_COLOR),
            ('BACKGROUND', (0,54), (10,54), _HEADER_COLOR),
            ('TEXTCOLOR', (0,5), (10,5), colors.white),
            ('TEXTCOLOR', (0,13), (10,13), colors.white),
            ('TEXTCOLOR', (0,19), (10,19), colors.white),
            ('TEXTCOLOR', (0,27), (10,27), colors.white),
            ('TEXTCOLOR', (0,32), (10,32), colors.white),
            ('TEXTCOLOR', (0,37), (10,37), colors.white),
            ('TEXTCOLOR', (0,43), (10,43), colors.white),
            ('TEXTCOLOR', (0,48), (10,48), colors.white),
            ('TEXTCOLOR', (0,54), (10,54), colors.white),
            ('FONTNAME', (0,5), (10,5), 'Helvetica-Bold'),
            # Título Grande
            ('FONTSIZE', (3,1), (10,2), 16),
            ('FONTNAME', (3,1), (10,2), 'Helvetica-Bold'),
            ('ALIGN', (3,1), (10,2), 'CENTER'),
        ]

        t = Table(matrix, colWidths=col_w, rowHeights=row_h)
        t.setStyle(TableStyle(style_list))
        
        tw, th = t.wrap(w - 2*mx, h)
        t.drawOn(c, mx, h - th - 0.5*cm)

        # Logos e QR
        if _LOGO_PATH.exists():
            c.drawImage(str(_LOGO_PATH), mx + 0.2*cm, h - 1.8*cm, width=4*cm, preserveAspectRatio=True, mask='auto')
        if _QR_PATH.exists():
            c.drawImage(str(_QR_PATH), w - mx - 2.5*cm, h - 1.8*cm, width=2.2*cm, preserveAspectRatio=True, mask='auto')

        # Rodapé
        c.setFont("Helvetica", 7)
        c.drawString(mx + 0.5*cm, 1.5*cm, "Assinatura do Cliente ___________________________")
        c.drawString(w/2 + 0.5*cm, 1.5*cm, "Assinatura do Representante Alisul ___________________________")
        c.drawString(mx + 0.5*cm, 2.5*cm, f"Local e Data: {_s(cli.faturamento_municipio)}/SP, {datetime.now().strftime('%d/%m/%Y')}")

        c.save()
        buffer.seek(0)
        return buffer.read()

    except Exception as e:
        logger.error(f"Erro ao gerar PDF a partir do Excel: {e}", exc_info=True)
        raise RuntimeError(f"Erro técnico no PDF Supra: {str(e)}")
