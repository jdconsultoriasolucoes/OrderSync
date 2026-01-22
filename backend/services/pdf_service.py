# backend/services/pdf_service.py

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from pathlib import Path
import os
import io

from services.pedido_pdf_data import carregar_pedido_pdf
from models.pedido_pdf import PedidoPdf


# Paleta de cores (ajuste se quiser)
# OBS: aqui NÃO é mais vermelho; é um bege/marrom próximo do layout antigo
SUPRA_RED = colors.Color(0.78, 0.70, 0.60)       # faixa e cabeçalho da tabela
SUPRA_DARK = colors.Color(0.1, 0.1, 0.1)        # texto escuro
SUPRA_BG_LIGHT = colors.Color(0.95, 0.95, 0.95) # fundo clarinho


def _br_number(value, decimals=2, suffix=""):
    """
    Formata número no padrão brasileiro.
    """
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


# def gerar_pdf_pedido(pedido: PedidoPdf, sem_validade: bool = False) -> bytes:
#     buffer = io.BytesIO()
#     _desenhar_pdf(pedido, buffer, sem_validade=sem_validade)
#     buffer.seek(0)
#     return buffer.read()


def _desenhar_pdf(pedido: PedidoPdf, buffer: io.BytesIO, sem_validade: bool = False) -> None:
    """
    Desenha o PDF do pedido no arquivo `path`, usando layout corporativo.
    """
    # os.makedirs(os.path.dirname(path), exist_ok=True) # Not needed when writing to buffer

    # Página em modo paisagem (horizontal)
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize

    # margens
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm
    top_y = height - margin_y
    available_width = width - 2 * margin_x

    # estilo para textos longos (Observações)
    styles = getSampleStyleSheet()
    obs_style = styles["Normal"]
    obs_style.fontName = "Helvetica"
    obs_style.fontSize = 9
    obs_style.leading = 11

    # ============================
    # LOGO EM CIMA / FAIXA EMBAIXO
    # ============================
    base_dir = Path(__file__).resolve().parents[2]
    logo_path = base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png"

    if not logo_path.exists():
        # fallback genérico
        static_dir = base_dir / "frontend" / "public"
        for candidate in [
            static_dir / "logo_cliente_supra.png",
            static_dir / "logo.png",
        ]:
            if candidate.exists():
                logo_path = candidate
                break
        else:
            logo_path = None

    # Logo no canto direito superior (acima da faixa)
    logo_h = 0
    if logo_path and logo_path.exists():
        try:
            img = ImageReader(str(logo_path))
            logo_w = 3.0 * cm
            iw, ih = img.getSize()
            logo_h = logo_w * ih / iw
            x_logo = width - margin_x - logo_w
            y_logo = top_y - logo_h
            c.drawImage(
                img,
                x_logo,
                y_logo,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            logo_h = 0

    # Faixa horizontal (header corporativo)
    faixa_h = 1.2 * cm
    faixa_y = top_y - logo_h - 0.2 * cm
    c.setFillColor(SUPRA_RED)
    c.rect(margin_x, faixa_y - faixa_h, available_width, faixa_h, stroke=0, fill=1)

    # Texto na faixa
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(
        margin_x + 0.3 * cm,
        faixa_y - faixa_h + 0.35 * cm,
        "DIGITAÇÃO DO ORÇAMENTO"
    )

    # Data / Validade (Bloco direito do header)
    c.setFont("Helvetica", 10)
    
    # Start y for the right-aligned text block
    y_right_block_start = faixa_y - faixa_h + 0.35 * cm + 0.2 * cm

    c.setFont("Helvetica", 9) 
    c.drawRightString(width - margin_x - 0.3 * cm, y_right_block_start, f"Data do Pedido: {pedido.data_pedido.strftime('%d/%m/%Y')}")
    
    if not sem_validade and pedido.validade_tabela:
        c.drawRightString(width - margin_x - 0.3 * cm, y_right_block_start - 0.4 * cm, f"Proposta válida até: {pedido.validade_tabela}")

    # Atualiza y para baixo da faixa
    y = faixa_y - faixa_h - 0.5 * cm

    # =======================
    # BLOCO 1 - DADOS CLIENTE
    # =======================
    codigo_cliente = pedido.codigo_cliente or ""
    cliente = pedido.cliente or ""
    razao_social = pedido.nome_fantasia or ""

    # larguras em cm (aprox.):
    label_cod_w = 1.4 * cm
    cod_val_w   = 3.5 * cm        # código ~5 cm
    label_cli_w = 2.0 * cm
    label_raz_w = 2.3 * cm

    restante    = available_width - (label_cod_w + cod_val_w + label_cli_w + label_raz_w)
    cli_val_w   = max(restante * 0.55, 6.0 * cm)
    raz_val_w   = max(restante * 0.45, 5.0 * cm)

    bloco1_col_widths = [
        label_cod_w, cod_val_w,
        label_cli_w, cli_val_w,
        label_raz_w, raz_val_w,
    ]

    bloco1_data = [[
        "Código:", str(codigo_cliente),
        "Cliente:", cliente[:120],
        "Razão Social:", razao_social[:80],
    ]]

    bloco1_table = Table(bloco1_data, colWidths=bloco1_col_widths)
    bloco1_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SUPRA_BG_LIGHT),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "RIGHT"),  # "Código:"
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),  # "Cliente:"
                ("ALIGN", (4, 0), (4, 0), "RIGHT"),  # "Razão Social:"
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    _, bloco1_h = bloco1_table.wrap(available_width, height)
    bloco1_table.drawOn(c, margin_x, y - bloco1_h)
    y = y - bloco1_h - 0.3 * cm

    # =======================
    # BLOCO 2 - FRETE / DATA
    # =======================
    frete_total = float(pedido.frete_total or 0)
    frete_kg = float(pedido.frete_kg or 0)

    if pedido.data_entrega_ou_retirada:
        data_entrega_str = pedido.data_entrega_ou_retirada.strftime("%d/%m/%Y")
    else:
        data_entrega_str = ""

    # FRETE (agora mostra FRETE KG no topo - solicitado "inverter")
    if frete_kg > 0:
        frete_str = "R$ " + _br_number(frete_kg)
    else:
        frete_str = "R$ 0,00"

    frete_data = [
        ["Frete Total:", frete_str],
    ]
    frete_col_widths = [3.0 * cm, 4.0 * cm]

    frete_table = Table(frete_data, colWidths=frete_col_widths)
    frete_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ]
        )
    )

    # DATA DE RETIRADA/ENTREGA
    data_data = [
        ["Data Retirada/Entrega:", data_entrega_str],
    ]
    data_col_widths = [4.0 * cm, 5.0 * cm]

    data_table = Table(data_data, colWidths=data_col_widths)
    data_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ]
        )
    )

    y = y - 0.1 * cm
    bloco2_left_w = frete_col_widths[0] + frete_col_widths[1]
    bloco2_right_w = data_col_widths[0] + data_col_widths[1]
    bloco2_gap = available_width - bloco2_left_w - bloco2_right_w

    _, frete_h = frete_table.wrap(bloco2_left_w, height)
    _, data_h = data_table.wrap(bloco2_right_w, height)
    bloco2_h = max(frete_h, data_h)

    frete_table.drawOn(c, margin_x, y - frete_h)
    data_table.drawOn(c, margin_x + bloco2_left_w + bloco2_gap, y - data_h)
    y = y - bloco2_h + -0.3 * cm

    # =======================
    # TABELA DE ITENS (multi-página)
    # =======================
    header = [
        "Codigo",
        "Produto",
        "Embal",
        "Qtd",
        "Cond. Pgto",
        "Comissão",
        "Valor Retira",
        "Valor Entrega",
    ]

    # ordena itens por quantidade (maior -> menor)
    itens_ordenados = sorted(
        pedido.itens,
        key=lambda it: float(getattr(it, "quantidade", 0) or 0),
        reverse=True,
    )

    # converte itens em linhas da tabela
    all_rows = []
    for it in itens_ordenados:
        all_rows.append(
            [
                it.codigo,
                it.produto,
                it.embalagem or "",
                f"{it.quantidade:g}",
                it.condicao_pagamento or "",
                it.tabela_comissao or "",
                "R$ " + _br_number(float(it.valor_retira or 0)),
                "R$ " + _br_number(float(it.valor_entrega or 0)),
            ]
        )

    # Larguras base em cm; escala para ocupar a largura inteira
    base_widths_cm = [
        1.7,  # Código
        8.3,  # Produto
        1.8,  # Embalagem
        1.5,  # Qtd
        5.5,  # Cond. Pgto
        2.7,  # Comissão
        2.5,  # Valor Retira
        2.5,  # Valor Entrega
    ]
    total_base = sum(base_widths_cm)
    scale = (available_width / cm) / total_base
    col_widths = [w * scale * cm for w in base_widths_cm]

    # estilo da tabela de itens (reutilizado em todas as páginas)
    itens_table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.black),

            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (3, 1), (3, -1), "CENTER"),   # Qtd
            ("ALIGN", (6, 1), (7, -1), "RIGHT"),    # valores
        ]
    )

    itens_x = margin_x
    current_y = y  # posição vertical atual para itens

    # quebra em várias páginas, se necessário
    rows_buffer = []

    def _desenhar_tabela_pagina(rows, y_top):
        if not rows:
            return y_top
        data_page = [header] + rows
        table = Table(data_page, colWidths=col_widths)
        table.setStyle(itens_table_style)
        _, table_height = table.wrap(available_width, height)
        table.drawOn(c, itens_x, y_top - table_height)
        return y_top - table_height - 0.5 * cm

    for row in all_rows:
        # testa se cabe adicionar mais uma linha nesta página
        teste_rows = rows_buffer + [row]
        data_test = [header] + teste_rows
        table_test = Table(data_test, colWidths=col_widths)
        table_test.setStyle(itens_table_style)
        _, test_height = table_test.wrap(available_width, height)

        if current_y - test_height < margin_y:
            # não cabe -> desenha o que já temos nesta página
            current_y = _desenhar_tabela_pagina(rows_buffer, current_y)
            rows_buffer = []

            # nova página somente com continuação dos itens (sem cabeçalho do pedido)
            c.showPage()
            current_y = height - margin_y

        rows_buffer.append(row)

    # desenha o resto (última página de itens)
    current_y = _desenhar_tabela_pagina(rows_buffer, current_y)

    # atualiza y global para a próxima seção (fechamento/observações)
    y = current_y

    # =======================
    # FECHAMENTO + OBSERVAÇÕES
    # =======================
    obs_text = (pedido.observacoes or "").strip()

    # largura dos dois blocos na mesma linha
    gap = 0.3 * cm
    fech_block_width = available_width * 0.45   # fechamento à esquerda
    obs_block_width = available_width - fech_block_width - gap

    # NOVO: Peso Bruto vs Liquido
    total_peso_liq_raw = getattr(pedido, "total_peso_liquido", 0.0) or 0.0
    total_peso_bru_raw = getattr(pedido, "total_peso_bruto", 0.0) or 0.0

    def _fmt_peso(p):
        return _br_number(int(p + 0.5) if p >= 0 else int(p - 0.5), 0, " kg")

    total_valor = float(pedido.total_valor or 0)

    data_fech = [
        ["Fechamento do Orçamento:", ""],
        ["Total em Peso Líquido:", _fmt_peso(total_peso_liq_raw)],
        ["Total em Peso Bruto:",   _fmt_peso(total_peso_bru_raw)],
        ["Valor Frete:", "R$ " + _br_number(frete_total)],
        ["Total em Valor:", "R$ " + _br_number(total_valor)],
    ]

    fech_col_widths = [fech_block_width * 0.6, fech_block_width * 0.4]

    fech_table = Table(data_fech, colWidths=fech_col_widths)
    fech_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ]
        )
    )

    # Observações (DIREITA, SEMPRE APARECE) – com quebra de linha automática
    obs_text = (pedido.observacoes or "").strip()
    obs_para = Paragraph(obs_text.replace("\n", "<br/>"), obs_style)

    data_obs = [["Observações:", obs_para]]
    obs_col_widths = [2.8 * cm, obs_block_width - 2.8 * cm]

    obs_table = Table(data_obs, colWidths=obs_col_widths)
    obs_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), SUPRA_BG_LIGHT),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), SUPRA_DARK),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ]
        )
    )

    # desenha lado a lado na mesma "altura"
    y_top = y
    fech_x = itens_x
    obs_x = itens_x + fech_block_width + gap

    _, fech_h = fech_table.wrap(fech_block_width, height)
    _, obs_h = obs_table.wrap(obs_block_width, height)
    max_h = max(fech_h, obs_h)

    # se não couber na página atual, joga fechamento/obs para a próxima página
    if y_top - max_h < margin_y:
        c.showPage()
        y_top = height - margin_y
        fech_x = itens_x
        obs_x = itens_x + fech_block_width + gap

    fech_table.drawOn(c, fech_x, y_top - fech_h)
    obs_table.drawOn(c, obs_x, y_top - obs_h)

    y = y_top - max_h - 0.3 * cm

    # rodapé
    c.setFont("Helvetica", 8)
    c.drawString(itens_x, y, "Documento gerado automaticamente pelo OrderSync.")
    
    if sem_validade:
        c.drawCentredString(width / 2, 1 * cm, "*Confirmação da Solicitação de Orçamento *")


    c.showPage()
    c.save()


def gerar_pdf_pedido(*args, destino_dir: str = "/tmp", sem_validade: bool = False, **kwargs) -> bytes:
    """
    Gera PDF do pedido.
    Assinaturas suportadas:
    1) gerar_pdf_pedido(pedido_pdf: PedidoPdf, sem_validade=...) -> bytes
    2) gerar_pdf_pedido(db: Session, pedido_id: int, sem_validade=...) -> bytes
    """
    pedido = None
    
    # Caso 1: Passou objeto PedidoPdf direto
    if len(args) == 1:
        if isinstance(args[0], PedidoPdf):
            pedido = args[0]
        # Se for Session, cai no logic abaixo? Não, Session é arg 0.
        # Vamos checar types.
    
    # Caso 2: Passou (db, pedido_id)
    if not pedido and len(args) >= 2:
        db = args[0]
        pid = args[1]
        pedido = carregar_pedido_pdf(db, int(pid))
        
    # Caso kwargs (db=..., pedido_id=...)
    if not pedido and "db" in kwargs and "pedido_id" in kwargs:
         pedido = carregar_pedido_pdf(kwargs["db"], int(kwargs["pedido_id"]))

    if not pedido:
         # Tenta recuperar do args[0] se for PedidoPdf, pois a checagem len(args)==1 pode falhar se passarem mais args opcionais
         if len(args) > 0 and isinstance(args[0], PedidoPdf):
             pedido = args[0]
         else:
             raise TypeError("Uso inválido de gerar_pdf_pedido. Espetado (PedidoPdf) ou (db, id).")

    # Override do sem_validade se vier no kwargs
    if "sem_validade" in kwargs:
        sem_validade = kwargs["sem_validade"]

    # Gera em memória (mais rápido e seguro que File IO)
    buffer = io.BytesIO()
    _desenhar_pdf(pedido, buffer, sem_validade=sem_validade)
    buffer.seek(0)
    return buffer.read()


def gerar_pdf_lista_preco(pedido: PedidoPdf) -> bytes:
    """
    Gera PDF estilo 'Lista de Preço' (sem Qtd, sem Obs, valores com/sem frete).
    """
    buffer = io.BytesIO()
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm

    # 1) Cabeçalho simplificado (Faixa)
    c.setFillColor(SUPRA_RED)
    faixa_h = 1.0 * cm
    faixa_y = height - margin_y - faixa_h
    available_width = width - 2 * margin_x
    c.rect(margin_x, faixa_y, available_width, faixa_h, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x + 0.3 * cm, faixa_y + 0.3 * cm, "LISTA DE PREÇOS")

    # Data
    c.setFont("Helvetica", 10)
    data_str = pedido.data_pedido.strftime('%d/%m/%Y')
    c.drawRightString(width - margin_x - 0.3 * cm, faixa_y + 0.3 * cm, f"Data: {data_str}")

    # Cliente
    y = faixa_y - 0.5 * cm
    c.setFillColor(SUPRA_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, f"Cliente: {pedido.cliente or ''}") 
    if pedido.nome_fantasia:
         c.drawString(margin_x, y - 0.4*cm, f"Fantasia: {pedido.nome_fantasia}")
         y -= 0.4*cm
    
    y -= 1.0 * cm

    # 2) Tabela Itens
    # Colunas: Código | Produto | Embal | R$ Sem Frete | R$ Com Frete
    # Sem Quantidade, Sem Obs.
    
    # 2) Tabela Itens
    # Colunas: Código | Produto | Embal | Cond. | MK% | R$ C/Frete | MK C/F | R$ S/Frete | MK S/F
    
    header = ["Cód", "Produto", "Embal", "Cond.", "MK%", "R$ C/Frete", "MK C/F", "R$ S/Frete", "MK S/F"]
    
    # Prepara dados
    itens_ordenados = sorted(pedido.itens, key=lambda it: it.produto or "")

    data_rows = []
    for it in itens_ordenados:
        markup_pct = it.markup or 0
        mk_str = f"{markup_pct:g}%" if markup_pct else "0%"
        
        # Unit Values (using explicit fields from saving logic)
        val_unit = float(it.valor_retira or 0)
        frete_unit = float(it.valor_entrega or 0)
        
        # R$ C/Frete (Cost w/ Freight) = Unit + Freight
        # CORRECTION: valor_entrega already contains (Price + Freight) in link_pedido context
        custo_cf = frete_unit
        
        # MK C/F (Final Price w/ Freight)
        venda_cf = float(it.valor_final_markup or 0)
        if venda_cf <= 0: venda_cf = custo_cf # fallback

        # R$ S/Frete (Cost w/o Freight) = Unit
        custo_sf = val_unit

        # MK S/F (Final Price w/o Freight)
        venda_sf = float(it.valor_s_frete_markup or 0)
        if venda_sf <= 0: venda_sf = custo_sf # fallback

        data_rows.append([
            it.codigo or "",
            it.produto or "",
            it.embalagem or "",
            it.condicao_pagamento or "",
            mk_str,
            _br_number(custo_cf),
            _br_number(venda_cf),
            _br_number(custo_sf),
            _br_number(venda_sf),
        ])
    
    col_widths = [
        1.6 * cm, # Cód
        7.0 * cm, # Produto
        2.0 * cm, # Embal
        5.5 * cm, # Cond
        1.2 * cm, # MK%
        2.2 * cm, # R$ C/Frete
        2.2 * cm, # MK C/F
        2.2 * cm, # R$ S/Frete
        2.2 * cm  # MK S/F
    ]
    # Ajusta largura total para ocupar available_width
    current_sum = sum(col_widths)
    scale = available_width / current_sum
    final_widths = [w * scale for w in col_widths]

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SUPRA_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 7), # Fonte um pouco menor pra caber
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"), # Alinha valores à direita
    ])

    rows_buffer = []
    current_y = y
    
    def _draw_page(rows, y_pos):
        tbl = Table([header] + rows, colWidths=final_widths)
        tbl.setStyle(table_style)
        _, h_tbl = tbl.wrap(available_width, height)
        tbl.drawOn(c, margin_x, y_pos - h_tbl)
        return y_pos - h_tbl

    for row in data_rows:
        test_tbl = Table([header] + rows_buffer + [row], colWidths=final_widths)
        test_tbl.setStyle(table_style)
        _, h_test = test_tbl.wrap(available_width, height)
        
        if current_y - h_test < margin_y:
            # Quebra página
            _draw_page(rows_buffer, current_y)
            c.showPage()
            current_y = height - margin_y
            rows_buffer = [row]
        else:
            rows_buffer.append(row)

    if rows_buffer:
        _draw_page(rows_buffer, current_y)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
