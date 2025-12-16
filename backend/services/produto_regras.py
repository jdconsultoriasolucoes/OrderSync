# services/produto_regras.py

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text


def _sincronizar_um_grupo(
    db: Session,
    fornecedor: str,
    lista: str,
) -> Dict[str, int]:
    """
    Sincroniza a lista ativa de (fornecedor, lista) da t_preco_produto_pdf_v2
    com a tabela t_cadastro_produto_v2.

    Regras:
      - join: codigo (intermediária) x codigo_supra (produto)
              + fornecedor
              + lista (intermediária) x tipo (produto)
      - atualiza: preco, preco_tonelada, validade_tabela
                  (guardando preco_anterior e preco_tonelada_anterior)
      - inativa: produtos de (fornecedor, tipo=lista) que não estão na lista ativa
      - insere: itens que estão na lista ativa e não têm produto ainda
    """
    fornecedor = fornecedor.strip()
    lista = lista.strip()

    stats = {
        "atualizados": 0,
        "inativados": 0,
        "inseridos": 0,
    }

    # 1) Atualizar produtos que BATEM no join
    update_sql = text(
        """
        WITH lista_ativa AS (
            SELECT
                fornecedor,
                lista,
                codigo,
                familia,
                descricao,
                preco_ton,
                preco_sc,
                validade_tabela
            FROM public.t_preco_produto_pdf_v2
            WHERE ativo = TRUE
              AND fornecedor = :fornecedor
              AND lista = :lista
        )
        UPDATE public.t_cadastro_produto_v2 AS p
           SET preco_anterior          = p.preco,
               preco_tonelada_anterior = p.preco_tonelada,
               preco                   = la.preco_sc,
               preco_tonelada          = la.preco_ton,
               validade_tabela         = la.validade_tabela
        FROM lista_ativa AS la
        WHERE p.fornecedor   = la.fornecedor
          AND p.tipo         = la.lista
          AND p.codigo_supra = la.codigo
        """
    )

    res = db.execute(update_sql, {"fornecedor": fornecedor, "lista": lista})
    stats["atualizados"] = res.rowcount or 0

    # 2) Inativar produtos que sumiram da lista ativa
    inativar_sql = text(
        """
        UPDATE public.t_cadastro_produto_v2 AS p
           SET status_produto = 'NÃO ATIVO'
        WHERE p.fornecedor = :fornecedor
          AND p.tipo       = :lista
          AND p.codigo_supra NOT IN (
                SELECT codigo
                FROM public.t_preco_produto_pdf_v2
                WHERE ativo = TRUE
                  AND fornecedor = :fornecedor
                  AND lista = :lista
          )
        """
    )

    res = db.execute(inativar_sql, {"fornecedor": fornecedor, "lista": lista})
    stats["inativados"] = res.rowcount or 0

    # 3) Inserir produtos novos (estão na lista ativa e não existem na base)
    inserir_sql = text(
        """
        WITH lista_ativa AS (
            SELECT
                fornecedor,
                lista,
                familia,
                codigo,
                descricao,
                preco_ton,
                preco_sc,
                validade_tabela
            FROM public.t_preco_produto_pdf_v2
            WHERE ativo = TRUE
              AND fornecedor = :fornecedor
              AND lista = :lista
        ),
        nao_cadastrados AS (
            SELECT la.*
            FROM lista_ativa la
            LEFT JOIN public.t_cadastro_produto_v2 p
              ON  p.fornecedor   = la.fornecedor
              AND p.tipo         = la.lista
              AND p.codigo_supra = la.codigo
            WHERE p.id IS NULL
        )
        INSERT INTO public.t_cadastro_produto_v2 (
            tipo,
            familia,
            codigo_supra,
            nome_produto,
            preco_tonelada,
            preco,
            validade_tabela,
            fornecedor,
            status_produto,
            created_at,
            updated_at
        )
        SELECT
            lista              AS tipo,
            familia            AS familia,
            codigo             AS codigo_supra,
            descricao          AS nome_produto,
            preco_ton          AS preco_tonelada,
            preco_sc           AS preco,
            validade_tabela    AS validade_tabela,
            fornecedor         AS fornecedor,
            'ATIVO'            AS status_produto,
            NOW()              AS created_at,
            NOW()              AS updated_at
        FROM nao_cadastrados
        """
    )

    res = db.execute(inserir_sql, {"fornecedor": fornecedor, "lista": lista})
    stats["inseridos"] = res.rowcount or 0

    db.commit()
    return stats


def sincronizar_produtos_com_listas_ativas(
    db: Session,
    fornecedor: Optional[str] = None,
    lista: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Roda a sincronização para todas as combinações (fornecedor, lista)
    com linhas ATIVAS na t_preco_produto_pdf_v2.

    Se 'fornecedor' e/ou 'lista' forem informados, filtra o escopo.
    """
    params: Dict[str, Any] = {}
    conds: List[str] = ["ativo = TRUE"]

    if fornecedor:
        conds.append("fornecedor = :fornecedor")
        params["fornecedor"] = fornecedor.strip()

    if lista:
        conds.append("lista = :lista")
        params["lista"] = lista.strip()

    where_sql = " AND ".join(conds)

    combos_sql = text(
        f"""
        SELECT DISTINCT fornecedor, lista
        FROM public.t_preco_produto_pdf_v2
        WHERE {where_sql}
        ORDER BY fornecedor, lista
        """
    )

    rows = db.execute(combos_sql, params).fetchall()

    resumo: Dict[str, Any] = {
        "total_grupos": len(rows),
        "grupos": [],
    }

    for fornecedor_val, lista_val in rows:
        stats = _sincronizar_um_grupo(db, fornecedor_val, lista_val)
        resumo["grupos"].append(
            {
                "fornecedor": fornecedor_val,
                "lista": lista_val,
                **stats,
            }
        )

    return resumo
