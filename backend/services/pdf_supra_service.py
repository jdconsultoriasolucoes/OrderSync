"""
backend/services/pdf_supra_service.py
Gera a Ficha de Cadastro Alisul em PDF com fidelidade absoluta (Pixel-Perfect Grid).
Baseado na geometria extraída do template Excel oficial.
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

# Assets
_BASE = Path(__file__).resolve().parent.parent / "assets"
_LOGO_PATH  = _BASE / "img_aba_Cadastro_Parte_1_0.png"
_QR_PATH    = _BASE / "img_aba_Cadastro_Parte_1_1.png"

# Paleta e Design
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

def _get_page1_grid():
    """Retorna geometria, spans e cores da Página 1."""
    u = 0.144 * cm # Unidade calibrada para K colunas em A4
    col_w = [9.71*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 13*u, 12.14*u]
    
    # Alturas aproximadas baseado na extração (points to pt)
    row_h = [15]*65 
    # Ajustes finos de linhas de título
    for i in [5, 13, 23, 31, 37, 43, 48, 54, 60]: row_h[i] = 22 # Cabeçalhos
    for i in [4, 18, 22, 26, 32, 36]: row_h[i] = 4 # Espaçadores finos do Excel

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

def _get_page2_grid():
    """Retorna geometria, spans e cores da Página 2."""
    u = 0.170 * cm # Ajustado para 11 colunas da Aba 2
    col_w = [8.71*u, 13*u, 13*u, 13*u, 13.71*u, 8.0*u, 12.71*u, 8.71*u, 13*u, 13*u, 10.71*u]
    row_h = [15]*45
    
    spans = [
        ('SPAN', (7, 27), (10, 27)), ('SPAN', (3, 3), (9, 3)), ('SPAN', (4, 27), (6, 27)),
        ('SPAN', (0, 7), (3, 7)), ('SPAN', (0, 14), (1, 14)), ('SPAN', (7, 26), (10, 26)),
        ('SPAN', (0, 38), (10, 38)), ('SPAN', (3, 34), (10, 34)), ('SPAN', (7, 23), (10, 23)),
        ('SPAN', (0, 35), (10, 35)), ('SPAN', (4, 6), (10, 6)), ('SPAN', (2, 25), (3, 25)),
        ('SPAN', (0, 44), (10, 44)), ('SPAN', (2, 12), (5, 12)), ('SPAN', (0, 5), (10, 5)),
        ('SPAN', (0, 15), (1, 15)), ('SPAN', (2, 28), (3, 28)), ('SPAN', (2, 19), (9, 19)),
        ('SPAN', (7, 25), (10, 25)), ('SPAN', (4, 26), (6, 26)), ('SPAN', (2, 24), (3, 24)),
        ('SPAN', (0, 40), (10, 40)), ('SPAN', (4, 25), (6, 25)), ('SPAN', (6, 12), (10, 12)),
        ('SPAN', (0, 23), (3, 23)), ('SPAN', (2, 21), (9, 21)), ('SPAN', (7, 28), (10, 28)),
        ('SPAN', (0, 34), (2, 34)), ('SPAN', (3, 33), (6, 33)), ('SPAN', (2, 14), (5, 14)),
        ('SPAN', (0, 36), (10, 36)), ('SPAN', (4, 24), (6, 24)), ('SPAN', (2, 13), (5, 13)),
        ('SPAN', (0, 24), (1, 26)), ('SPAN', (0, 20), (1, 20)), ('SPAN', (0, 17), (10, 17)),
        ('SPAN', (0, 27), (1, 28)), ('SPAN', (4, 7), (10, 7)), ('SPAN', (2, 20), (9, 20)),
        ('SPAN', (2, 18), (10, 18)), ('SPAN', (6, 14), (10, 14)), ('SPAN', (0, 11), (10, 11)),
        ('SPAN', (7, 24), (10, 24)), ('SPAN', (2, 26), (3, 26)), ('SPAN', (7, 33), (10, 33)),
        ('SPAN', (0, 32), (10, 32)), ('SPAN', (6, 13), (10, 13)), ('SPAN', (2, 15), (5, 15)),
        ('SPAN', (0, 13), (1, 13)), ('SPAN', (0, 41), (10, 41)), ('SPAN', (0, 6), (3, 6)),
        ('SPAN', (0, 31), (10, 31)), ('SPAN', (0, 33), (2, 33)), ('SPAN', (10, 19), (10, 21)),
        ('SPAN', (0, 21), (1, 21)), ('SPAN', (0, 19), (1, 19)), ('SPAN', (4, 23), (6, 23)),
        ('SPAN', (0, 18), (1, 18)), ('SPAN', (6, 15), (10, 15)), ('SPAN', (0, 42), (10, 42)),
        ('SPAN', (0, 37), (10, 37)), ('SPAN', (3, 1), (10, 2)), ('SPAN', (2, 27), (3, 27)),
        ('SPAN', (0, 12), (1, 12)), ('SPAN', (0, 43), (10, 43)), ('SPAN', (4, 28), (6, 28)),
        ('SPAN', (0, 39), (10, 39)), ('SPAN', (0, 30), (10, 30))
    ]
    return col_w, row_h, spans

def gerar_pdf_cliente_supra(cli) -> bytes:
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        mx = 0.5*cm
        
        # --- PÁGINA 1: DADOS CADASTRAIS E PATRIMÔNIO ---
        col_w, row_h, spans = _get_page1_grid()
        matrix = [["" for _ in range(11)] for _ in range(65)]
        
        # Mapeamento Data-Driven Página 1
        matrix[7][0] = f"Nome do Cliente: {_s(cli.cadastro_nome_cliente)}"
        matrix[8][0] = f"Denominação Comercial/Fantasia: {_s(cli.cadastro_nome_fantasia)}"
        matrix[9][0] = f"Telefone: {_s(cli.compras_telefone_fixo_responsavel)}"
        matrix[10][0] = f"Celular: {_s(cli.compras_celular_responsavel)}"
        matrix[10][4] = f"E-mail: {_s(cli.compras_email_resposavel)}"
        matrix[11][0] = f"CNPJ: {_s(cli.cadastro_cnpj)}"
        matrix[12][0] = f"CPF: {_s(cli.cadastro_cpf)}"
        matrix[12][4] = f"INSC. ESTADUAL: {_s(cli.cadastro_inscricao_estadual)}"
        
        # Endereço Entrega (A21 etc no Excel) -> Row 20
        matrix[20][0] = f"Av./Rua/Nro: {_s(cli.entrega_endereco)}"
        matrix[20][8] = f"CEP: {_s(cli.entrega_cep)}"
        matrix[21][0] = f"Bairro: {_s(cli.entrega_bairro)}"
        matrix[21][5] = f"Cidade: {_s(cli.entrega_municipio)}"
        matrix[21][8] = f"Estado: {_s(cli.entrega_estado)}"

        # Endereço Cobrança (A25 etc) -> Row 24
        matrix[24][0] = f"Av./Rua/Nro: {_s(cli.cobranca_endereco)}"
        matrix[24][8] = f"CEP: {_s(cli.cobranca_cep)}"
        matrix[25][0] = f"Bairro: {_s(cli.cobranca_bairro)}"
        matrix[25][5] = f"Cidade: {_s(cli.cobranca_municipio)}"
        matrix[25][8] = f"Estado: {_s(cli.cobranca_estado)}"

        # Referências Bancárias (A34) -> Row 33
        matrix[33][0] = f"A) Banco: {_s(cli.ref_bancaria_banco)}"
        matrix[33][2] = f"Ag: {_s(cli.ref_bancaria_agencia)}"
        matrix[33][4] = f"Conta: {_s(cli.ref_bancaria_conta)}"

        # Referências Comerciais (A40) -> Row 39
        matrix[39][0] = f"A) Empresa: {_s(cli.ref_comercial_empresa)}"
        matrix[39][4] = f"Cidade: {_s(cli.ref_comercial_cidade)}"
        matrix[39][6] = f"Fone: {_s(cli.ref_comercial_telefone)}"
        matrix[39][8] = f"Contato: {_s(cli.ref_comercial_contato)}"

        # Patrimônio (A46) -> Row 45
        matrix[45][0] = f"Bens Imóveis: {_s(cli.bem_imovel_imovel)}"
        matrix[45][2] = f"Local: {_s(cli.bem_imovel_localizacao)}"
        matrix[45][5] = f"Área: {_s(cli.bem_imovel_area)}"
        matrix[45][7] = f"Valor: {_br_number(cli.bem_imovel_valor, 2, ' R$')}"
        matrix[45][9] = f"Hipot: {_s(cli.bem_imovel_hipotecado)}"

        # Plantel (A51) -> Row 50
        matrix[50][0] = f"Espécie: {_s(cli.animal_especie)}"
        matrix[50][5] = f"Nro Animais: {_s(cli.animal_numero)}"
        matrix[50][7] = f"Consumo Dia: {_s(cli.animal_consumo_diario)}"
        matrix[50][9] = f"Mes: {_s(cli.animal_consumo_mensal)}"

        # Títulos de Seção (Marrom) - Texto exato do Excel
        matrix[5][0] = "FICHA CADASTRAL - Página 1/2"
        matrix[13][0] = "LOCALIZAÇÃO E ENTREGA"
        matrix[23][0] = "LOCALIZAÇÃO E COBRANÇA"
        matrix[31][0] = "CONTATOS INTERNOS PARA VENDAS E COBRANÇAS"
        matrix[37][0] = "REFERÊNCIAS BANCÁRIAS E COMERCIAIS"
        matrix[43][0] = "PATRIMÔNIO E ATIVIDADE"
        matrix[48][0] = "PLANTEL DE ANIMAIS"
        matrix[54][0] = "RECOMENDAÇÕES DO DEPARTAMENTO DE VENDAS :"

        # Estilização do Grid Página 1
        style_list = spans + [
            ('GRID', (0,5), (10,64), 0.4, colors.grey),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 6.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            # Cabeçalhos Marrons
            ('BACKGROUND', (0,5), (7,5), _HEADER_COLOR),
            ('BACKGROUND', (0,13), (10,13), _HEADER_COLOR),
            ('BACKGROUND', (0,23), (10,23), _HEADER_COLOR),
            ('BACKGROUND', (0,31), (10,31), _HEADER_COLOR),
            ('BACKGROUND', (0,37), (10,37), _HEADER_COLOR),
            ('BACKGROUND', (0,43), (10,43), _HEADER_COLOR),
            ('BACKGROUND', (0,48), (10,48), _HEADER_COLOR),
            ('BACKGROUND', (0,54), (10,54), _HEADER_COLOR),
            ('TEXTCOLOR', (0,5), (10,5), colors.white),
            ('TEXTCOLOR', (0,13), (10,13), colors.white),
            ('TEXTCOLOR', (0,23), (10,23), colors.white),
            ('TEXTCOLOR', (0,31), (10,31), colors.white),
            ('TEXTCOLOR', (0,37), (10,37), colors.white),
            ('TEXTCOLOR', (0,43), (10,43), colors.white),
            ('TEXTCOLOR', (0,48), (10,48), colors.white),
            ('TEXTCOLOR', (0,54), (10,54), colors.white),
        ]
        
        t1 = Table(matrix, colWidths=col_w, rowHeights=row_h)
        t1.setStyle(TableStyle(style_list))
        
        # Posicionamento
        tw, th = t1.wrap(w - 2*mx, h)
        t1.drawOn(c, mx, h - th - 1*cm)

        # Assets
        if _LOGO_PATH.exists():
            c.drawImage(str(_LOGO_PATH), w - 5.5*cm, h - 1.5*cm, width=5*cm, height=1.3*cm, preserveAspectRatio=True)
        if _QR_PATH.exists():
            c.drawImage(str(_QR_PATH), mx + 0.2*cm, 1*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True)
            c.setFont("Helvetica", 6)
            c.drawString(mx + 3*cm, 3*cm, "Portal de Privacidade Alisul / Termos LGPD")
            c.drawString(mx + 3*cm, 2*cm, "Assinatura do Cliente: __________________________________________________  Data: ___/___/___")

        c.showPage()
        
        # --- PÁGINA 2: USO INTERNO E COMERCIAL ---
        col_w_2, row_h_2, spans_2 = _get_page2_grid()
        matrix2 = [["" for _ in range(11)] for _ in range(45)]
        
        # Mapeamento Página 2
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

        # Títulos Pág 2
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
        logger.error(f"Erro Crítico na geração Grid-PDF: {e}", exc_info=True)
        raise RuntimeError(f"Falha técnica na renderização 'Identical Layout': {str(e)}")
