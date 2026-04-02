"""
backend/services/pdf_supra_service.py
Gera a Ficha de Cadastro Alisul (v.2024/02) em PDF usando ReportLab.
Refatoração Sênior: Tratamento de exceções, formatação padronizada e logs.
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

# Configuração de Logs
logger = logging.getLogger("ordersync.pdf_supra")

# ---------------------------------------------------------------------------
# Recursos e Identidade Visual
# ---------------------------------------------------------------------------
_BASE = Path(__file__).resolve().parent.parent / "assets"
_LOGO_PATH  = _BASE / "img_aba_Cadastro_Parte_1_0.png"
_QR_PATH    = _BASE / "img_aba_Cadastro_Parte_1_1.png"

# Paleta oficial identificada no mapeamento
_HEADER_COLOR = colors.Color(0.502, 0.251, 0.0)   # Marrom Alisul
_LIGHT_GRAY   = colors.Color(0.93, 0.93, 0.93)
_DARK_GRAY    = colors.Color(0.30, 0.30, 0.30)


def _br_number(value, decimals=2, suffix="") -> str:
    """Formata número no padrão brasileiro (1.234,56)."""
    if value is None:
        return "0,00" + suffix
    try:
        value = float(value)
        fmt = f"{{:,.{decimals}f}}"
        s = fmt.format(value).replace(",", "X").replace(".", ",").replace("X", ".")
        return s + suffix
    except (TypeError, ValueError):
        return "0,00" + suffix


def _s(value, default="") -> str:
    """Conversor robusto para string."""
    if value is None:
        return default
    return str(value).strip()


def _draw_section_header(c, x, y, w, h, title, font_size=8):
    """Renderiza barras de título de seção com a cor oficial."""
    c.setFillColor(_HEADER_COLOR)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x + 0.2*cm, y + 0.12*cm, title)
    c.setFillColor(colors.black)


def _draw_field(c, x, y, label, value, font_size=8):
    """Renderiza par Label: Valor com tipografia mista."""
    c.setFont("Helvetica-Bold", font_size)
    label_w = c.stringWidth(label, "Helvetica-Bold", font_size)
    c.drawString(x, y, label)
    c.setFont("Helvetica", font_size)
    c.drawString(x + label_w + 3, y, _s(value))


def _table_style():
    """Gera o estilo base para tabelas de dados na ficha."""
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), _HEADER_COLOR),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [_LIGHT_GRAY, colors.white]),
    ])


def _pagina1(c: canvas.Canvas, cli, width, height):
    """Renderiza a Página 1: Dados Cadastrais e Patrimônio."""
    mx, my = 1.0*cm, 1.0*cm
    cw = width - 2*mx
    y = height - my

    # Cabeçalho e Logo
    if _LOGO_PATH.exists():
        try:
            img = ImageReader(str(_LOGO_PATH))
            c.drawImage(img, width - mx - 3.5*cm, y - 1.2*cm, width=3.5*cm, height=1.2*cm, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            logger.warning(f"Falha ao renderizar logo Alisul no PDF: {e}")

    c.setFont("Helvetica-Bold", 13)
    c.drawString(mx, y - 0.6*cm, "FICHA CADASTRAL")
    c.setFont("Helvetica", 9)
    c.drawString(mx, y - 1.1*cm, f"Página 1/2  —  v.2024/02  |  Gerado em: {datetime.now().strftime('%d/%m/%Y')}")
    y -= 1.6*cm

    sh, line_h = 0.45*cm, 0.50*cm
    pad = 0.1*cm

    # ---- DADOS CADASTRAIS ----
    _draw_section_header(c, mx, y - sh, cw, sh, "DADOS CADASTRAIS")
    y -= (sh + 0.08*cm)
    
    campos = [
        [("Nome Cliente:", cli.cadastro_nome_cliente), ("Nome Fantasia:", cli.cadastro_nome_fantasia)],
        [("Telefone:", getattr(cli, 'compras_telefone_fixo_responsavel', '')), ("Celular:", getattr(cli, 'compras_celular_responsavel', ''))],
        [("CNPJ:", cli.cadastro_cnpj), ("E-mail:", cli.compras_email_resposavel)],
        [("CPF:", cli.cadastro_cpf), ("Insc.Estadual:", cli.cadastro_inscricao_estadual)]
    ]
    for row in campos:
        c.setFillColor(_LIGHT_GRAY)
        c.rect(mx, y - line_h, cw, line_h, fill=1, stroke=0)
        c.setFillColor(colors.black)
        _draw_field(c, mx + pad, y - line_h + 0.12*cm, row[0][0], row[0][1])
        _draw_field(c, mx + cw*0.5 + pad, y - line_h + 0.12*cm, row[1][0], row[1][1])
        y -= line_h

    # ---- ENDEREÇOS ----
    y -= 0.15*cm
    _draw_section_header(c, mx, y - sh, cw, sh, "ENDEREÇO DE ENTREGA")
    y -= (sh + 0.08*cm)
    end_ent = f"{_s(cli.entrega_endereco)}, {_s(cli.entrega_bairro)} - {_s(cli.entrega_municipio)}/{_s(cli.entrega_estado)} (CEP: {_s(cli.entrega_cep)})"
    _draw_field(c, mx + pad, y - line_h + 0.12*cm, "Local:", end_ent)
    y -= line_h

    _draw_section_header(c, mx, y - sh, cw, sh, "ENDEREÇO DE COBRANÇA")
    y -= (sh + 0.08*cm)
    end_cob = f"{_s(cli.cobranca_endereco)}, {_s(cli.cobranca_bairro)} - {_s(cli.cobranca_municipio)}/{_s(cli.cobranca_estado)} (CEP: {_s(cli.cobranca_cep)})"
    _draw_field(c, mx + pad, y - line_h + 0.12*cm, "Local:", end_cob)
    y -= line_h

    # ---- REFERÊNCIAS ----
    y -= 0.15*cm
    _draw_section_header(c, mx, y - sh, cw, sh, "REFERÊNCIAS BANCÁRIAS E COMERCIAIS")
    y -= (sh + 0.08*cm)
    _draw_field(c, mx + pad, y - line_h + 0.12*cm, "Banco:", f"{_s(cli.ref_bancaria_banco)} / Ag: {_s(cli.ref_bancaria_agencia)} / Conta: {_s(cli.ref_bancaria_conta)}")
    y -= line_h
    _draw_field(c, mx + pad, y - line_h + 0.12*cm, "Comercial:", f"{_s(cli.ref_comercial_empresa)} ({_s(cli.ref_comercial_cidade)}) - Tel: {_s(cli.ref_comercial_telefone)}")
    y -= line_h

    # ---- PATRIMÔNIO ----
    y -= 0.15*cm
    _draw_section_header(c, mx, y - sh, cw, sh, "PATRIMÔNIO E PLANTEL")
    y -= (sh + 0.08*cm)
    _draw_field(c, mx + pad, y - line_h + 0.12*cm, "Bens Imóveis:", f"{_s(cli.bem_imovel_imovel)} | Valor: {_br_number(cli.bem_imovel_valor, 2, ' R$')}")
    y -= line_h
    _draw_field(c, mx + pad, y - line_h + 0.12*cm, "Plantel:", f"{_s(cli.animal_especie)} ({_s(cli.animal_numero)} cab.) | Consumo: {_s(cli.animal_consumo_diario)} kg/dia")
    y -= line_h

    # ---- LGPD E ASSINATURA ----
    y_lgpd = 1.0*cm + 2.5*cm
    if _QR_PATH.exists():
        try:
            c.drawImage(str(_QR_PATH), mx, y_lgpd, width=2.2*cm, height=2.2*cm, mask='auto', preserveAspectRatio=True)
        except: pass

    lgpd_txt = (
        "Declaro que as informações prestadas nesta ficha são verdadeiras e autênticas. "
        "Fico ciente das Políticas de Privacidade e Uso de Dados da Alisul Alimentos S/A, "
        "disponibilizada via QR Code, autorizando o tratamento de meus dados para fins comerciais."
    )
    c.setFont("Helvetica", 6.5)
    text_obj = c.beginText(mx + 2.5*cm, y_lgpd + 1.8*cm)
    text_obj.setLeading(8)
    # Quebra simples
    text_obj.textLine(lgpd_txt[:100])
    text_obj.textLine(lgpd_txt[100:])
    c.drawText(text_obj)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(mx + 2.5*cm, y_lgpd + 0.2*cm, "Assinatura do Cliente: _________________________________________  Data: ___/___/___")


def _pagina2(c: canvas.Canvas, cli, width, height):
    """Renderiza a Página 2: Uso Interno, Canais e Estrutura Comercial."""
    mx, my = 1.0*cm, 1.0*cm
    cw = width - 2*mx
    y = height - my

    c.setFont("Helvetica-Bold", 13)
    c.drawString(mx, y - 0.6*cm, "FICHA CADASTRAL — USO INTERNO")
    y -= 1.5*cm

    sh = 0.45*cm

    # ---- CANAL DE VENDAS ----
    _draw_section_header(c, mx, y - sh, cw, sh, "ESTRUTURA COMERCIAL E CANAIS")
    y -= sh + 0.08*cm

    cv_data = [
        ["Classe", "Canal de Venda / Lista de Preço", "Vendedor / Supervisor", "Comissão"],
        ["PET",     _s(cli.canal_pet),   _s(cli.supervisor_nome_pet),    _s(cli.comissao_pet)],
        ["FROST",   _s(cli.canal_frost), "",                             ""],
        ["INSUMOS", _s(cli.canal_insumos), _s(cli.supervisor_nome_insumo), _s(cli.comissao_insumos)]
    ]
    cv_table = Table(cv_data, colWidths=[cw*0.13, cw*0.35, cw*0.32, cw*0.20])
    cv_table.setStyle(_table_style())
    tw, th = cv_table.wrap(cw, height)
    cv_table.drawOn(c, mx, y - th)
    y -= th + 0.5*cm

    # ---- ANÁLISE DE CRÉDITO ----
    _draw_section_header(c, mx, y - sh, cw, sh, "ANÁLISE DE CRÉDITO E FINANCEIRO")
    y -= (sh + 0.1*cm)
    
    line_h = 0.50*cm
    pad = 0.1*cm
    
    fin_fields = [
        ("Limite Solicitado:", _br_number(cli.elaboracao_limite_credito, 2, " R$")),
        ("Forma Pagamento:",   _s(cli.cadastro_tipo_compra)),
        ("Classificação:",    _s(cli.elaboracao_classificacao)),
        ("Tipo de Operação:",  _s(cli.elaboracao_tipo_venda))
    ]
    for lbl, val in fin_fields:
        c.setFillColor(_LIGHT_GRAY)
        c.rect(mx, y - line_h, cw, line_h, fill=1, stroke=0)
        c.setFillColor(colors.black)
        _draw_field(c, mx + pad, y - line_h + 0.12*cm, lbl, val)
        y -= line_h

    # ---- VISTOS INTERNOS ----
    y -= 1.0*cm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(mx, y, "Visto Gerência Vendas: _______________________")
    c.drawString(mx + cw*0.5, y, "Visto Crédito: _______________________")


def gerar_pdf_cliente_supra(cli) -> bytes:
    """Entry point centralizado para geração do PDF."""
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Página 1
        _pagina1(c, cli, width, height)
        c.showPage()

        # Página 2
        _pagina2(c, cli, width, height)
        c.showPage()

        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        logger.error(f"Erro fatal na geração do PDF Supra (ID: {cli.id}): {e}", exc_info=True)
        raise RuntimeError(f"Falha técnica ao gerar arquivo PDF: {str(e)}")
