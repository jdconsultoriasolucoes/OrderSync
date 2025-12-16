# services/produto_relatorio.py

from __future__ import annotations

from typing import Any, Dict, List, Optional
from io import BytesIO
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


# -------------------------------------------------
# Helpers de formatação
# -------------------------------------------------
def _fmt_moeda(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:.2f}%".replace(".", ",")


# -------------------------------------------------
# Coleta de dados para o relatório
# -------------------------------------------------
def coletar_dados_relatorio_lista(
    db: Session,
    fornecedor: str,
    lista: str,
) -> Dict[str, Any]:
    """
    Monta a estrutura de dados para o relatório de alterações
    de uma determinada combinação (fornecedor, lista).

    Usa:
      - t_preco_produto_pdf_v2 (apenas linhas ATIVAS)
      - t_cadastro_produto_v2  (estado pós-sincronização)

    Classificação:
      - aumentos: preco > preco_anterior
      - reducoes: preco < preco_anterior
      - novos: preco_anterior IS NULL
      - inativados: status_produto = 'NÃO ATIVO'
                    e não constam na lista ativa atual
    """
    fornecedor = fornecedor.strip()
    lista = lista.strip()

    params = {"fornecedor": fornecedor, "lista": lista}

    # ---------------------------
    # Metadados da ingestão
    # ---------------------------
    sql_meta = text(
        """
        SELECT
            MAX(validade_tabela) AS validade_tabela,
            MAX(data_ingestao)   AS data_ingestao,
            MAX(nome_arquivo)    AS nome_arquivo,
            COUNT(*)             AS total_itens
        FROM public.t_preco_produto_pdf_v2
        WHERE ativo = TRUE
          AND fornecedor = :fornecedor
          AND lista = :lista
        """
    )
    meta = db.execute(sql_meta, params).mappings().first() or {}

    validade_tabela = meta.get("validade_tabela")
    data_ingestao = meta.get("data_ingestao")
    nome_arquivo = meta.get("nome_arquivo")
    total_itens = int(meta.get("total_itens") or 0)

    # Se não tiver nada ativo, devolve vazio
    if total_itens == 0:
        return {
            "fornecedor": fornecedor,
            "lista": lista,
            "validade_tabela": validade_tabela,
            "data_ingestao": data_ingestao,
            "nome_arquivo": nome_arquivo,
            "total_itens_lista": 0,
            "aumentos": [],
            "reducoes": [],
            "novos": [],
            "inativados": [],
        }

    # -------------------------------------------------------
    # Produtos que constam na lista ativa + tabela de produto
    # -------------------------------------------------------
    # Aqui pegamos o estado pós-sincronização:
    #  - preco_anterior / preco
    #  - preco_tonelada_anterior / preco_tonelada (se quiser usar depois)
    sql_produtos_lista = text(
        """
        SELECT
            p.codigo_supra        AS codigo,
            p.nome_produto        AS nome,
            p.preco_anterior      AS preco_anterior,
            p.preco               AS preco_novo,
            p.preco_tonelada_anterior AS preco_ton_anterior,
            p.preco_tonelada      AS preco_ton_novo
        FROM public.t_cadastro_produto_v2 p
        JOIN public.t_preco_produto_pdf_v2 t
          ON t.ativo       = TRUE
         AND t.fornecedor  = :fornecedor
         AND t.lista       = :lista
         AND t.codigo      = p.codigo_supra
         AND t.fornecedor  = p.fornecedor
         AND t.lista       = p.tipo
        """
    )

    produtos_lista = db.execute(sql_produtos_lista, params).mappings().all()

    aumentos: List[Dict[str, Any]] = []
    reducoes: List[Dict[str, Any]] = []
    novos: List[Dict[str, Any]] = []

    for row in produtos_lista:
        codigo = row["codigo"]
        nome = row["nome"]
        preco_ant = row["preco_anterior"]
        preco_novo = row["preco_novo"]
        preco_ton_ant = row["preco_ton_anterior"]
        preco_ton_novo = row["preco_ton_novo"]

        # NOVO produto (não tinha preco_anterior)
        if preco_ant is None:
            novos.append(
                {
                    "codigo": codigo,
                    "nome": nome,
                    "preco_novo": preco_novo,
                    "preco_ton_novo": preco_ton_novo,
                }
            )
            continue

        # Produto existente -> calcular variação (se tiver preco_novo)
        if preco_novo is None:
            # sem preço novo, não entra em variação; podemos ignorar
            continue

        try:
            dif = preco_novo - preco_ant
        except Exception:
            # Se der erro de operação (ex: decimal invalido), assume sem diferença
            dif = 0

        var_pct = None
        if preco_ant not in (0, None):
            try:
                # cast to float to prevent "Decimal * float" error or InvalidOperation
                var_pct = float(dif / preco_ant) * 100.0
            except Exception:
                var_pct = 0.0

        dif_ton = None
        var_pct_ton = None
        if preco_ton_ant not in (0, None) and preco_ton_novo not in (None,):
            try:
                dif_ton = preco_ton_novo - preco_ton_ant
                var_pct_ton = float(dif_ton / preco_ton_ant) * 100.0
            except Exception:
                var_pct_ton = 0.0

        info = {
            "codigo": codigo,
            "nome": nome,
            "preco_anterior": preco_ant,
            "preco_novo": preco_novo,
            "var_pct": var_pct,
            "preco_ton_anterior": preco_ton_ant,
            "preco_ton_novo": preco_ton_novo,
            "var_pct_ton": var_pct_ton,
        }

        if dif > 0:
            aumentos.append(info)
        elif dif < 0:
            reducoes.append(info)
        # se dif == 0, não entra (sem alteração); se quiser,
        # dá pra criar uma lista separado mais pra frente

    # -------------------------------------------------------
    # Produtos inativados
    # -------------------------------------------------------
    sql_inativados = text(
        """
        SELECT
            p.codigo_supra   AS codigo,
            p.nome_produto   AS nome,
            p.preco          AS preco_ultimo,
            p.preco_tonelada AS preco_ton_ultimo
        FROM public.t_cadastro_produto_v2 p
        WHERE p.fornecedor = :fornecedor
          AND p.tipo       = :lista
          AND p.status_produto = 'NÃO ATIVO'
          AND p.codigo_supra NOT IN (
                SELECT codigo
                FROM public.t_preco_produto_pdf_v2
                WHERE ativo = TRUE
                  AND fornecedor = :fornecedor
                  AND lista = :lista
          )
        """
    )

    inativados_rows = db.execute(sql_inativados, params).mappings().all()
    inativados: List[Dict[str, Any]] = [
        {
            "codigo": r["codigo"],
            "nome": r["nome"],
            "preco_ultimo": r["preco_ultimo"],
            "preco_ton_ultimo": r["preco_ton_ultimo"],
        }
        for r in inativados_rows
    ]

    return {
        "fornecedor": fornecedor,
        "lista": lista,
        "validade_tabela": validade_tabela,
        "data_ingestao": data_ingestao,
        "nome_arquivo": nome_arquivo,
        "total_itens_lista": total_itens,
        "aumentos": aumentos,
        "reducoes": reducoes,
        "novos": novos,
        "inativados": inativados,
    }


# -------------------------------------------------
# Geração de PDF
# -------------------------------------------------
# -------------------------------------------------
# Geração de PDF (Estilo "Pedidão" / Clássico)
# -------------------------------------------------
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from pathlib import Path

# Paleta "Clássica" (igual pdf_service.py)
SUPRA_RED = colors.Color(0.78, 0.70, 0.60)       # Bege/Marrom ("Red" no nome legado)
SUPRA_DARK = colors.Color(0.1, 0.1, 0.1)
SUPRA_BG_LIGHT = colors.Color(0.95, 0.95, 0.95)

def gerar_pdf_relatorio_lista(
    db: Session,
    fornecedor: str,
    lista: str,
) -> bytes:
    """
    Gera PDF com visual tabular (clean/spreadsheet style) similar ao de Pedidos.
    """
    dados = coletar_dados_relatorio_lista(db, fornecedor, lista)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- LOGO (tentativa de encontrar) ---
    base_dir = Path(__file__).resolve().parents[2] # backend/../
    logo_path = None
    candidates = [
        base_dir / "frontend" / "public" / "tabela_preco" / "logo_cliente_supra.png",
        base_dir / "frontend" / "public" / "logo_cliente_supra.png", 
        base_dir / "frontend" / "public" / "logo.png"
    ]
    for cand in candidates:
        if cand.exists():
            logo_path = cand
            break
            
    if logo_path:
        # Logo redimensionado (max width 4cm, max height 2cm)
        im = Image(str(logo_path))
        im_w, im_h = im.imageWidth, im.imageHeight
        aspect = im_h / float(im_w)
        target_w = 4 * cm
        target_h = target_w * aspect
        im.drawWidth = target_w
        im.drawHeight = target_h
        im.hAlign = 'RIGHT'
        elements.append(im)
        elements.append(Spacer(1, 0.5 * cm))

    # --- TÍTULO ---
    title_style = styles["Heading1"]
    title_style.alignment = 1 # Center
    elements.append(Paragraph("Relatório de Alterações de Lista de Preços", title_style))
    elements.append(Spacer(1, 0.5 * cm))
    
    # --- CABEÇALHO (Metadados) ---
    # Faremos uma tabela simples de 2 colunas para ficar organizado
    validade = dados.get("validade_tabela")
    val_str = validade.strftime("%d/%m/%Y") if isinstance(validade, datetime) or hasattr(validade, 'strftime') else str(validade or "-")
    
    data_ing = dados.get("data_ingestao")
    ing_str = data_ing.strftime("%d/%m/%Y") if isinstance(data_ing, datetime) or hasattr(data_ing, 'strftime') else str(data_ing or "-")

    meta_data = [
        ["Fornecedor:", dados.get("fornecedor") or "-"],
        ["Lista:", dados.get("lista") or "-"],
        ["Validade Tabela:", val_str],
        ["Data Ingestão:", ing_str],
        ["Arquivo:", dados.get("nome_arquivo") or "-"],
        ["Itens Hoje:", str(dados.get("total_itens_lista") or 0)],
    ]
    
    table_meta = Table(meta_data, colWidths=[4*cm, 10*cm])
    table_meta.setStyle(TableStyle([
        # ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(table_meta)
    elements.append(Spacer(1, 1*cm))
    
    # --- RESUMO (Box destacado) ---
    aumentos = dados["aumentos"]
    reducoes = dados["reducoes"]
    novos = dados["novos"]
    inativados = dados["inativados"]
    
    summary_data = [
        ["RESUMO DAS ALTERAÇÕES", ""],
        ["Produtos com Aumento:", str(len(aumentos))],
        ["Produtos com Redução:", str(len(reducoes))],
        ["Produtos Novos:", str(len(novos))],
        ["Produtos Inativados:", str(len(inativados))],
    ]
    
    table_summary = Table(summary_data, colWidths=[6*cm, 3*cm], hAlign='LEFT')
    table_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_RED),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
    ]))
    elements.append(table_summary)
    elements.append(Spacer(1, 1*cm))
    
    # --- FUNÇÃO AUXILIAR PARA TABELAS DE DADOS ---
    def add_data_section(title, rows, col_names, col_widths):
        if not rows:
            return

        elements.append(Paragraph(title, styles["Heading3"]))
        elements.append(Spacer(1, 0.2*cm))
        
        # Prepara dados (Header + Rows)
        table_data = [col_names] + rows
        
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Estilo "Pedidão"
        ts = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SUPRA_RED),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ])
        
        # Alinhamento específico (assumindo colunas de valores no final)
        # Ex: Cod(0), Nome(1), Val(2), Val(3), %(4) -> 2,3,4 align RIGHT
        # Vamos generalizar: colunas > 1 são números geralmente (exceto inativados que tem "-" no meio)
        # Mas vamos fixar pelo nome das colunas se possível, ou pelo índice fixo dos templates abaixo.
        
        t.setStyle(ts)
        elements.append(t)
        elements.append(Spacer(1, 0.8*cm))

    # --- TABELA AUMENTOS ---
    # Cols: Código, Nome, Anterior, Novo, Var%
    rows_aum = [[
        i["codigo"], 
        i["nome"][:55], 
        _fmt_moeda(i["preco_anterior"]), 
        _fmt_moeda(i["preco_novo"]), 
        _fmt_pct(i["var_pct"])
    ] for i in aumentos]
    
    if rows_aum:
        t = Table([["Código", "Produto", "Anterior", "Novo", "Var %"]] + rows_aum, 
                  colWidths=[2.5*cm, 7.5*cm, 2.5*cm, 2.5*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SUPRA_RED),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Valores à direita
        ]))
        elements.append(Paragraph("Produtos com AUMENTO", styles["Heading3"]))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(t)
        elements.append(Spacer(1, 0.8*cm))

    # --- TABELA REDUÇÕES ---
    rows_red = [[
        i["codigo"], 
        i["nome"][:55], 
        _fmt_moeda(i["preco_anterior"]), 
        _fmt_moeda(i["preco_novo"]), 
        _fmt_pct(i["var_pct"])
    ] for i in reducoes]
    
    if rows_red:
        t = Table([["Código", "Produto", "Anterior", "Novo", "Var %"]] + rows_red, 
                  colWidths=[2.5*cm, 7.5*cm, 2.5*cm, 2.5*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SUPRA_RED), # ou verde? melhor manter padrão
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(Paragraph("Produtos com REDUÇÃO", styles["Heading3"]))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(t)
        elements.append(Spacer(1, 0.8*cm))

    # --- TABELA NOVOS ---
    rows_new = [[
        i["codigo"], 
        i["nome"][:60], 
        _fmt_moeda(i["preco_novo"])
    ] for i in novos]
    
    if rows_new:
        t = Table([["Código", "Produto", "Novo Preço"]] + rows_new, 
                  colWidths=[3*cm, 10*cm, 4*cm], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SUPRA_RED),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(Paragraph("Produtos NOVOS", styles["Heading3"]))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(t)
        elements.append(Spacer(1, 0.8*cm))
        
    # --- TABELA INATIVADOS ---
    rows_ina = [[
        i["codigo"], 
        i["nome"][:60], 
        _fmt_moeda(i["preco_ultimo"])
    ] for i in inativados]
    
    if rows_ina:
        t = Table([["Código", "Produto", "Último Preço"]] + rows_ina, 
                  colWidths=[3*cm, 10*cm, 4*cm], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SUPRA_RED),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(Paragraph("Produtos INATIVADOS (Saíram da lista)", styles["Heading3"]))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(t)
        elements.append(Spacer(1, 0.8*cm))

    # Build PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
