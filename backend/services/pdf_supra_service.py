"""
backend/services/pdf_supra_service.py
Gera a Ficha de Cadastro Alisul em PDF com fidelidade absoluta (Pixel-Perfect Grid).
Baseado na geometria TOTAL (Row 1 to 65) do template Excel oficial.
"""
import io
import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

logger = logging.getLogger("ordersync.pdf_supra")

# Assets (Caminhos relativos para o Render)
_BASE = Path(__file__).resolve().parent.parent / "assets"
_LOGO_PATH  = _BASE / "img_aba_Cadastro_Parte_1_0.png"
_QR_PATH    = _BASE / "img_aba_Cadastro_Parte_1_1.png"

# Design
_HEADER_COLOR = colors.Color(128/255, 64/255, 0) # Marrom Alisul
_LIGHT_GRAY   = colors.Color(0.93, 0.93, 0.93)

def _br_number(value, decimals=2, suffix="") -> str:
    if value in [None, ""]: return "0,00" + suffix
    try:
        val = float(value)
        return f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suffix
    except: return "0,00" + suffix

def _s(val, default="") -> str:
    return str(val).strip() if val is not None else default

def _get_page1_config():
    """Geometria milimetrica para espelhar o Excel A1:K65."""
    u = 0.142 * cm
    col_w = [9.71*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 12.14*u]
    # Alturas reais extraidas via script (points converted to points/row)
    row_h = [13.5]*65
    for i in range(7, 13): row_h[i] = 23.25 # Area de dados cadastrais maior
    for i in [4, 18, 22, 26, 30, 36, 42, 47, 53, 59]: row_h[i] = 4.0 # Espaçadores finos

    # Todos os Spans (Gerados automaticamente via generate_spans.py)
    spans = [
        ('SPAN', (7, 52), (8, 52)), ('SPAN', (7, 34), (8, 34)), ('SPAN', (0, 14), (10, 14)),
        ('SPAN', (0, 23), (10, 23)), ('SPAN', (8, 55), (10, 55)), ('SPAN', (0, 12), (3, 12)),
        ('SPAN', (0, 5), (7, 5)), ('SPAN', (5, 21), (7, 21)), ('SPAN', (0, 57), (3, 57)),
        ('SPAN', (0, 24), (7, 24)), ('SPAN', (9, 52), (10, 52)), ('SPAN', (4, 11), (10, 11)),
        ('SPAN', (6, 56), (7, 56)), ('SPAN', (8, 16), (10, 16)), ('SPAN', (9, 44), (10, 44)),
        ('SPAN', (6, 17), (7, 17)), ('SPAN', (7, 51), (8, 51)), ('SPAN', (4, 33), (5, 33)),
        ('SPAN', (0, 25), (4, 25)), ('SPAN', (0, 32), (1, 32)), ('SPAN', (7, 44), (8, 44)),
        ('SPAN', (8, 58), (10, 58)), ('SPAN', (2, 35), (3, 35)), ('SPAN', (6, 57), (7, 57)),
        ('SPAN', (4, 35), (5, 35)), ('SPAN', (0, 40), (3, 40)), ('SPAN', (2, 16), (3, 16)),
        ('SPAN', (5, 28), (10, 28)), ('SPAN', (0, 34), (1, 34)), ('SPAN', (0, 55), (3, 55)),
        ('SPAN', (0, 51), (4, 51)), ('SPAN', (6, 62), (10, 62)), ('SPAN', (0, 62), (4, 62)),
        ('SPAN', (0, 27), (10, 27)), ('SPAN', (0, 41), (3, 41)), ('SPAN', (6, 58), (7, 58)),
        ('SPAN', (8, 21), (10, 21)), ('SPAN', (0, 44), (1, 44)), ('SPAN', (0, 59), (7, 59)),
        ('SPAN', (7, 49), (8, 49)), ('SPAN', (8, 20), (10, 20)), ('SPAN', (0, 60), (1, 60)),
        ('SPAN', (2, 45), (4, 45)), ('SPAN', (7, 33), (8, 33)), ('SPAN', (9, 33), (10, 33)),
        ('SPAN', (0, 6), (7, 6)), ('SPAN', (0, 45), (1, 45)), ('SPAN', (5, 44), (6, 44)),
        ('SPAN', (0, 58), (3, 58)), ('SPAN', (7, 35), (8, 35)), ('SPAN', (0, 10), (3, 10)),
        ('SPAN', (9, 35), (10, 35)), ('SPAN', (4, 39), (5, 39)), ('SPAN', (5, 46), (6, 46)),
        ('SPAN', (5, 45), (6, 45)), ('SPAN', (4, 12), (10, 12)), ('SPAN', (0, 28), (4, 28)),
        ('SPAN', (9, 45), (10, 45)), ('SPAN', (9, 50), (10, 50)), ('SPAN', (3, 1), (10, 2)),
        ('SPAN', (2, 17), (3, 17)), ('SPAN', (4, 57), (5, 57)), ('SPAN', (4, 17), (5, 17)),
        ('SPAN', (5, 29), (10, 29)), ('SPAN', (8, 24), (10, 24)), ('SPAN', (0, 33), (1, 33)),
        ('SPAN', (2, 33), (3, 33)), ('SPAN', (6, 41), (7, 41)), ('SPAN', (0, 48), (10, 48)),
        ('SPAN', (5, 25), (7, 25)), ('SPAN', (0, 35), (1, 35)), ('SPAN', (4, 38), (5, 38)),
        ('SPAN', (6, 38), (7, 38)), ('SPAN', (0, 38), (3, 38)), ('SPAN', (8, 38), (10, 38)),
        ('SPAN', (5, 49), (6, 49)), ('SPAN', (9, 34), (10, 34)), ('SPAN', (0, 49), (4, 49)),
        ('SPAN', (4, 58), (5, 58)), ('SPAN', (8, 39), (10, 39)), ('SPAN', (0, 31), (10, 31)),
        ('SPAN', (0, 13), (10, 13)), ('SPAN', (0, 21), (4, 21)), ('SPAN', (0, 7), (7, 7)),
        ('SPAN', (4, 56), (5, 56)), ('SPAN', (9, 49), (10, 49)), ('SPAN', (0, 11), (3, 11)),
        ('SPAN', (4, 40), (5, 40)), ('SPAN', (0, 9), (7, 9)), ('SPAN', (6, 40), (7, 40)),
        ('SPAN', (8, 25), (10, 25)), ('SPAN', (8, 56), (10, 56)), ('SPAN', (0, 56), (3, 56)),
        ('SPAN', (9, 51), (10, 51)), ('SPAN', (4, 55), (5, 55)), ('SPAN', (4, 10), (10, 10)),
        ('SPAN', (8, 6), (10, 6)), ('SPAN', (6, 55), (7, 55)), ('SPAN', (0, 8), (7, 8)),
        ('SPAN', (0, 29), (4, 29)), ('SPAN', (8, 40), (10, 40)), ('SPAN', (2, 32), (3, 32)),
        ('SPAN', (4, 32), (5, 32)), ('SPAN', (0, 50), (4, 50)), ('SPAN', (4, 41), (5, 41)),
        ('SPAN', (8, 17), (10, 17)), ('SPAN', (8, 57), (10, 57)), ('SPAN', (4, 16), (5, 16)),
        ('SPAN', (0, 16), (1, 17)), ('SPAN', (6, 16), (7, 16)), ('SPAN', (2, 34), (3, 34)),
        ('SPAN', (4, 34), (5, 34)), ('SPAN', (0, 39), (3, 39)), ('SPAN', (8, 41), (10, 41)),
        ('SPAN', (7, 45), (8, 45)), ('SPAN', (5, 50), (6, 50)), ('SPAN', (7, 50), (8, 50)),
        ('SPAN', (2, 60), (10, 60)), ('SPAN', (0, 20), (7, 20)), ('SPAN', (0, 54), (10, 54)),
        ('SPAN', (8, 59), (10, 59)), ('SPAN', (0, 46), (1, 46)), ('SPAN', (7, 46), (8, 46)),
        ('SPAN', (9, 46), (10, 46)), ('SPAN', (5, 51), (6, 51)), ('SPAN', (8, 5), (10, 5)),
        ('SPAN', (0, 52), (4, 52)), ('SPAN', (0, 19), (10, 19)), ('SPAN', (2, 44), (4, 44)),
        ('SPAN', (7, 32), (8, 32)), ('SPAN', (0, 37), (10, 37)), ('SPAN', (9, 32), (10, 32)),
        ('SPAN', (6, 39), (7, 39)), ('SPAN', (0, 43), (10, 43)), ('SPAN', (5, 52), (6, 52)),
        ('SPAN', (2, 46), (4, 46))
    ]
    return col_w, row_h, spans

def gerar_pdf_cliente_supra(cli) -> bytes:
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        mx = 0.5*cm
        
        # --- PÁGINA 1: GRID INTEGRAL ---
        col_w, row_h, spans = _get_page1_config()
        matrix = [["" for _ in range(11)] for _ in range(65)]
        
        # Mapeamento do Cabeçalho Superior (Visual)
        matrix[3][3] = "FICHA CADASTRAL  -  Página 1/2" # Linha 4 aproximada
        matrix[3][10] = "v.2024/02"
        
        # Grid Oficial (Linhas 6 e 7 do Excel)
        matrix[5][0] = "COMERCIAL"
        matrix[5][8] = "Financeiro"
        matrix[6][0] = "Dados Cadastrais"
        matrix[6][8] = "Limite aprovado"

        # Dados Cadastrais
        matrix[7][0] = f"Nome do Cliente: {_s(cli.cadastro_nome_cliente)}"
        matrix[8][0] = f"Denominação Comercial/Fantasia: {_s(cli.cadastro_nome_fantasia)}"
        matrix[10][0] = f"Celular: {_s(cli.compras_celular_responsavel)}"
        matrix[10][4] = f"E-mail: {_s(cli.compras_email_resposavel)}"
        matrix[11][0] = f"CNPJ: {_s(cli.cadastro_cnpj)}"
        matrix[12][0] = f"CPF: {_s(cli.cadastro_cpf)}"
        matrix[12][4] = f"INSCR. ESTADUAL: {_s(cli.cadastro_inscricao_estadual)}"
        
        # Endereços (Matching do print)
        matrix[20][0] = f"Av./Rua/Nro: {_s(cli.entrega_endereco)}"
        matrix[20][8] = f"CEP: {_s(cli.entrega_cep)}"
        matrix[21][0] = f"Bairro: {_s(cli.entrega_bairro)}"
        matrix[21][5] = f"Cidade: {_s(cli.entrega_municipio)}"
        matrix[21][8] = f"Estado: {_s(cli.entrega_estado)}"

        # Financeiro (Caixa Direita)
        matrix[7][8] = f"R$ {_br_number(cli.elaboracao_limite_credito)}"

        # Cabeçalhos de Seção
        matrix[13][0] = "Endereço de Entrega"
        matrix[23][0] = "Endereço de Cobrança"
        matrix[31][0] = "Contatos"
        matrix[37][0] = "Referências Bancárias"
        matrix[43][0] = "Referências Comerciais"
        matrix[48][0] = "Bens Imóveis"
        matrix[54][0] = "Plantel de Animais"

        style_list = spans + [
            ('GRID', (0,5), (10,63), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            # Cores Oficiais
            ('BACKGROUND', (0,5), (7,5), _HEADER_COLOR), # COMERCIAL
            ('BACKGROUND', (8,5), (10,5), _HEADER_COLOR), # Financeiro
            ('TEXTCOLOR', (0,5), (10,5), colors.white),
            ('FONTNAME', (8,5), (10,5), 'Helvetica-Bold'),
            ('BACKGROUND', (0,13), (10,13), _HEADER_COLOR),
            ('BACKGROUND', (0,23), (10,23), _HEADER_COLOR),
            ('BACKGROUND', (0,31), (10,31), _HEADER_COLOR),
            ('BACKGROUND', (0,37), (10,37), _HEADER_COLOR),
            ('BACKGROUND', (0,43), (10,43), _HEADER_COLOR),
            ('BACKGROUND', (0,48), (10,48), _HEADER_COLOR),
            ('BACKGROUND', (0,54), (10,54), _HEADER_COLOR),
            ('ALIGN', (3,3), (10,3), 'CENTER'),
            ('FONTSIZE', (3,3), (10,3), 16),
            ('FONTNAME', (3,3), (10,3), 'Helvetica-Bold'),
        ]
        
        t1 = Table(matrix, colWidths=col_w, rowHeights=row_h)
        t1.setStyle(TableStyle(style_list))
        tw, th = t1.wrap(w - mx*2, h)
        t1.drawOn(c, mx, h - th - 0.5*cm)

        # Assets (Logo à Esquerda)
        if _LOGO_PATH.exists():
            c.drawImage(str(_LOGO_PATH), mx + 0.5*cm, h - 2*cm, width=4*cm, height=1.3*cm, preserveAspectRatio=True)
        
        # QR Code e Assinaturas (Baseados no Print)
        if _QR_PATH.exists():
            c.drawImage(str(_QR_PATH), w - 4.5*cm, 2*cm, width=4*cm, height=4*cm, preserveAspectRatio=True)

        c.setFont("Helvetica", 8)
        c.drawString(mx + 0.5*cm, 1.5*cm, "Assinatura do Cliente ___________________________")
        c.drawString(w/2 + 0.5*cm, 1.5*cm, "Assinatura do Representante Alisul ___________________________")
        c.drawString(mx + 0.5*cm, 2.5*cm, f"Local e Data: {_s(cli.faturamento_municipio)}/SP, {datetime.now().strftime('%d/%m/%Y')}")

        c.showPage()
        
        # --- PÁGINA 2: USO INTERNO E COMERCIAL (Aba 2) ---
        col_w_2, row_h_2, spans_2 = _get_page2_grid()
        matrix2 = [["" for _ in range(11)] for _ in range(45)]
        
        # Dados Página 2
        matrix2[6][4] = f"Razão Social: {_s(cli.cadastro_nome_cliente)}"
        matrix2[7][4] = f"Fantasia: {_s(cli.cadastro_nome_fantasia)}"
        
        # Canais (C14-16) -> Rows 13, 14, 15
        matrix2[13][2] = _s(cli.canal_pet)
        matrix2[14][2] = _s(cli.canal_frost)
        matrix2[15][2] = _s(cli.canal_insumos)
        
        # Comissões (C20-21) -> Rows 19, 20
        matrix2[19][2] = _s(cli.comissao_pet)
        matrix2[20][2] = _s(cli.comissao_insumos)

        # Supervisores (E25, H25) -> Row 24
        matrix2[24][4] = _s(cli.supervisor_nome_pet)
        matrix2[24][7] = _s(cli.supervisor_nome_insumo)

        # Análise Financeira (D34, D35) -> Rows 33, 34
        matrix2[33][3] = _s(cli.cadastro_tipo_compra)
        matrix2[34][3] = _br_number(cli.elaboracao_limite_credito, 2, " R$")

        # Títulos Pág 2 (Marrom)
        matrix2[5][0] = "FICHA CADASTRAL - Página 2/2"
        matrix2[11][0] = "ESTRUTURA COMERCIAL"
        matrix2[31][0] = "ANÁLISE FINANCEIRA"

        style_list_2 = spans_2 + [
            ('GRID', (0,5), (10,40), 0.4, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 6.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,5), (10,5), _HEADER_COLOR),
            ('BACKGROUND', (0,11), (10,11), _HEADER_COLOR),
            ('BACKGROUND', (0,31), (10,31), _HEADER_COLOR),
            ('TEXTCOLOR', (0,5), (10,5), colors.white),
            ('TEXTCOLOR', (0,11), (10,11), colors.white),
            ('TEXTCOLOR', (0,31), (10,31), colors.white),
        ]
        
        t2 = Table(matrix2, colWidths=col_w_2, rowHeights=row_h_2)
        t2.setStyle(TableStyle(style_list_2))
        
        tw2, th2 = t2.wrap(w - 2*mx, h)
        t2.drawOn(c, mx, h - th2 - 1*cm)

        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        logger.error(f"Erro Crítico Grid-Fidelity: {e}", exc_info=True)
        raise RuntimeError(f"Erro técnico no PDF Supra: {str(e)}")
