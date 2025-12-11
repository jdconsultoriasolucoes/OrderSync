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

        dif = preco_novo - preco_ant
        var_pct = None
        if preco_ant not in (0, None):
            var_pct = (dif / preco_ant) * 100.0

        dif_ton = None
        var_pct_ton = None
        if preco_ton_ant not in (0, None) and preco_ton_novo not in (None,):
            dif_ton = preco_ton_novo - preco_ton_ant
            var_pct_ton = (dif_ton / preco_ton_ant) * 100.0

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
def gerar_pdf_relatorio_lista(
    db: Session,
    fornecedor: str,
    lista: str,
) -> bytes:
    """
    Gera um PDF (bytes) com o relatório de alterações de preço
    para a combinação (fornecedor, lista).
    """
    dados = coletar_dados_relatorio_lista(db, fornecedor, lista)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Margens
    margem_esq = 2 * cm
    margem_top = height - 2 * cm
    linha_altura = 14  # px approx

    def nova_pagina():
        c.showPage()

    # Cabeçalho
    y = margem_top

    titulo = "Relatório de Alterações de Lista de Preços"
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margem_esq, y, titulo)
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(margem_esq, y, f"Fornecedor: {dados.get('fornecedor') or '-'}")
    y -= linha_altura
    c.drawString(margem_esq, y, f"Lista: {dados.get('lista') or '-'}")
    y -= linha_altura

    validade = dados.get("validade_tabela")
    if isinstance(validade, datetime):
        validade_str = validade.strftime("%d/%m/%Y")
    elif isinstance(validade, (str,)):
        validade_str = str(validade)
    elif validade is not None:
        try:
            validade_str = validade.strftime("%d/%m/%Y")  # date
        except Exception:
            validade_str = str(validade)
    else:
        validade_str = "-"

    data_ing = dados.get("data_ingestao")
    if isinstance(data_ing, datetime):
        data_ing_str = data_ing.strftime("%d/%m/%Y %H:%M")
    elif data_ing is not None:
        try:
            data_ing_str = data_ing.strftime("%d/%m/%Y")
        except Exception:
            data_ing_str = str(data_ing)
    else:
        data_ing_str = "-"

    c.drawString(margem_esq, y, f"Validade da tabela: {validade_str}")
    y -= linha_altura
    c.drawString(margem_esq, y, f"Data da ingestão: {data_ing_str}")
    y -= linha_altura

    nome_arquivo = dados.get("nome_arquivo") or "-"
    c.drawString(margem_esq, y, f"Arquivo importado: {nome_arquivo}")
    y -= linha_altura

    total_itens = dados.get("total_itens_lista") or 0
    c.drawString(margem_esq, y, f"Itens na lista ativa: {total_itens}")
    y -= linha_altura * 2

    # Resumo estatístico
    aumentos = dados["aumentos"]
    reducoes = dados["reducoes"]
    novos = dados["novos"]
    inativados = dados["inativados"]

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_esq, y, "Resumo:")
    y -= linha_altura

    c.setFont("Helvetica", 10)
    c.drawString(
        margem_esq,
        y,
        f"Produtos com aumento: {len(aumentos)}",
    )
    y -= linha_altura
    c.drawString(
        margem_esq,
        y,
        f"Produtos com redução: {len(reducoes)}",
    )
    y -= linha_altura
    c.drawString(
        margem_esq,
        y,
        f"Produtos novos: {len(novos)}",
    )
    y -= linha_altura
    c.drawString(
        margem_esq,
        y,
        f"Produtos inativados: {len(inativados)}",
    )
    y -= linha_altura * 2

    # Helper para desenhar tabelas simples com quebra de página
    def desenhar_tabela(
        titulo_secao: str,
        colunas: List[str],
        linhas: List[List[str]],
    ):
        nonlocal y

        if not linhas:
            return

        # Título da seção
        if y < 4 * linha_altura:
            nova_pagina()
            y = margem_top

        c.setFont("Helvetica-Bold", 11)
        c.drawString(margem_esq, y, titulo_secao)
        y -= linha_altura

        # Cabeçalho
        c.setFont("Helvetica-Bold", 9)
        x = margem_esq
        larguras = [4 * cm, 8 * cm, 3 * cm, 3 * cm, 2.5 * cm]  # ajusta p/ 5 colunas

        for i, col in enumerate(colunas):
            if i < len(larguras):
                c.drawString(x, y, col)
                x += larguras[i]
            else:
                c.drawString(x, y, col)
                x += 3 * cm
        y -= linha_altura

        c.setFont("Helvetica", 8)

        for linha in linhas:
            if y < 2 * linha_altura:
                nova_pagina()
                y = margem_top - linha_altura
                # redesenha cabeçalho
                c.setFont("Helvetica-Bold", 9)
                x = margem_esq
                for i, col in enumerate(colunas):
                    if i < len(larguras):
                        c.drawString(x, y, col)
                        x += larguras[i]
                    else:
                        c.drawString(x, y, col)
                        x += 3 * cm
                y -= linha_altura
                c.setFont("Helvetica", 8)

            x = margem_esq
            for i, val in enumerate(linha):
                txt = (val or "")[:40]
                if i < len(larguras):
                    c.drawString(x, y, txt)
                    x += larguras[i]
                else:
                    c.drawString(x, y, txt)
                    x += 3 * cm
            y -= linha_altura

        y -= linha_altura  # espaço extra após a tabela

    # --------------------------
    # Tabela: Aumentos
    # --------------------------
    linhas_aumento: List[List[str]] = []
    for it in aumentos:
        linhas_aumento.append(
            [
                it["codigo"],
                it["nome"],
                _fmt_moeda(it["preco_anterior"]),
                _fmt_moeda(it["preco_novo"]),
                _fmt_pct(it["var_pct"]),
            ]
        )

    desenhar_tabela(
        "Produtos com AUMENTO de preço",
        ["Código", "Nome", "Preço ant.", "Preço novo", "% var."],
        linhas_aumento,
    )

    # --------------------------
    # Tabela: Reduções
    # --------------------------
    linhas_reducao: List[List[str]] = []
    for it in reducoes:
        linhas_reducao.append(
            [
                it["codigo"],
                it["nome"],
                _fmt_moeda(it["preco_anterior"]),
                _fmt_moeda(it["preco_novo"]),
                _fmt_pct(it["var_pct"]),
            ]
        )

    desenhar_tabela(
        "Produtos com REDUÇÃO de preço",
        ["Código", "Nome", "Preço ant.", "Preço novo", "% var."],
        linhas_reducao,
    )

    # --------------------------
    # Tabela: Novos
    # --------------------------
    linhas_novos: List[List[str]] = []
    for it in novos:
        linhas_novos.append(
            [
                it["codigo"],
                it["nome"],
                "-",
                _fmt_moeda(it["preco_novo"]),
                "-",  # não há variação %
            ]
        )

    desenhar_tabela(
        "Produtos NOVOS",
        ["Código", "Nome", "Preço ant.", "Preço novo", "% var."],
        linhas_novos,
    )

    # --------------------------
    # Tabela: Inativados
    # --------------------------
    linhas_inativados: List[List[str]] = []
    for it in inativados:
        linhas_inativados.append(
            [
                it["codigo"],
                it["nome"],
                _fmt_moeda(it["preco_ultimo"]),
                "-",  # deixou de existir na lista
                "-",  # sem variação %
            ]
        )

    desenhar_tabela(
        "Produtos INATIVADOS",
        ["Código", "Nome", "Último preço", "Preço novo", "% var."],
        linhas_inativados,
    )

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
