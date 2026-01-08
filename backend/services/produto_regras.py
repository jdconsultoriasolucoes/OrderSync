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

    # -- 0) PREPARAÇÃO DE IDs DE FAMILIA --
    # Identificar famílias distintas NA LISTA ATIVA
    familias_pdf = db.execute(text("""
        SELECT DISTINCT familia 
        FROM public.t_preco_produto_pdf_v2 
        WHERE ativo=TRUE AND fornecedor=:f AND lista=:l AND familia IS NOT NULL
    """), {"f": fornecedor, "l": lista}).fetchall()
    
    familias_nomes = [row[0] for row in familias_pdf]
    mapa_familia_id = {}
    
    # Buscar IDs existentes globalmente
    if familias_nomes:
        ftxt = text("SELECT DISTINCT familia, id_familia FROM public.t_cadastro_produto_v2 WHERE familia IN :fams AND id_familia IS NOT NULL")
        existing_fams = db.execute(ftxt, {"fams": tuple(familias_nomes)}).fetchall()
        for f_nome, f_id in existing_fams:
            mapa_familia_id[f_nome] = f_id

    # Determinar MAX id atual para novos (FILTRADO POR TIPO)
    max_id = db.execute(
        text("SELECT MAX(id_familia) FROM public.t_cadastro_produto_v2 WHERE tipo = :lista"),
        {"lista": lista}
    ).scalar() or 0
    
    # Atribuir IDs para as novas
    familias_novas = [f for f in familias_nomes if f not in mapa_familia_id]
    familias_novas.sort()
    
    for f_novo in familias_novas:
        max_id += 10
        mapa_familia_id[f_novo] = max_id
        
    # Build CTE for mapping
    cte_body = ""
    binds = {}
    if mapa_familia_id:
        values_parts = []
        for i, (fname, fid) in enumerate(mapa_familia_id.items()):
            pname = f"fn_{i}"
            pid = f"fid_{i}"
            binds[pname] = fname
            binds[pid] = fid
            values_parts.append(f"(:{pname}, :{pid})")
        cte_body = ", ".join(values_parts)
    else:
        # Fallback dummy CTE if no families (shouldn't happen active lists usually have items)
        cte_body = "('RESERVED_DUMMY', 0)"

    # 1) Atualizar produtos que BATEM no join
    # Agora com CTE de familias para update do id_familia
    update_sql = text(
        f"""
        WITH map_fam(nome_fam, id_fam) AS (
            VALUES {cte_body}
        ),
        lista_ativa AS (
            SELECT
                l.fornecedor,
                l.lista,
                l.codigo,
                l.familia,
                l.descricao,
                l.preco_ton,
                l.preco_sc,
                l.validade_tabela,
                l.filhos,
                m.id_fam
            FROM public.t_preco_produto_pdf_v2 l
            LEFT JOIN map_fam m ON m.nome_fam = l.familia
            WHERE l.ativo = TRUE
              AND l.fornecedor = :fornecedor
              AND l.lista = :lista
        )
        UPDATE public.t_cadastro_produto_v2 AS p
           SET preco_anterior          = p.preco,
               preco_tonelada_anterior = p.preco_tonelada,
               preco                   = la.preco_sc,
               preco_tonelada          = la.preco_ton,
               validade_tabela         = la.validade_tabela,
               familia                 = la.familia,
               fornecedor              = la.fornecedor,
               filhos                  = la.filhos,
               id_familia              = COALESCE(p.id_familia, la.id_fam)
        FROM lista_ativa AS la
        WHERE TRIM(p.tipo) = la.lista
          AND TRIM(p.codigo_supra) = la.codigo
          AND (
            p.fornecedor = la.fornecedor
            OR p.fornecedor IS NULL
            OR p.fornecedor = ''
            OR p.fornecedor ILIKE '%' || la.fornecedor || '%'
          )
        """
    )
    
    # Merge params
    run_params = {**{"fornecedor": fornecedor, "lista": lista}, **binds}
    res = db.execute(update_sql, run_params)
    stats["atualizados"] = res.rowcount or 0

    # (Passo 1.1 removido pois foi incorporado no UPDATE acima)

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

    # 3) Inserir produtos novos
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

    inserir_sql = text(
        f"""
        WITH map_fam(nome_fam, id_fam) AS (
            VALUES {cte_body}
        ),
        lista_ativa AS (
            SELECT
                l.fornecedor,
                l.lista,
                l.familia,
                l.codigo,
                l.descricao,
                l.preco_ton,
                l.preco_sc,
                l.validade_tabela,
                l.filhos,
                m.id_fam
            FROM public.t_preco_produto_pdf_v2 l
            LEFT JOIN map_fam m ON m.nome_fam = l.familia
            WHERE l.ativo = TRUE
              AND l.fornecedor = :fornecedor
              AND l.lista = :lista
        ),
        nao_cadastrados AS (
            SELECT la.*
            FROM lista_ativa la
            LEFT JOIN public.t_cadastro_produto_v2 p
              ON  TRIM(p.tipo) = la.lista
              AND TRIM(p.codigo_supra) = la.codigo
              AND (
                  p.fornecedor = la.fornecedor
                  OR p.fornecedor IS NULL
                  OR p.fornecedor = ''
                  OR p.fornecedor ILIKE '%' || la.fornecedor || '%'
              )
            WHERE p.id IS NULL
        )
        INSERT INTO public.t_cadastro_produto_v2 (
            tipo,
            familia,
            id_familia,
            codigo_supra,
            nome_produto,
            preco_tonelada,
            preco,
            validade_tabela,
            fornecedor,
            status_produto,
            filhos,
            created_at,
            updated_at
        )
        SELECT
            lista,
            familia,
            id_fam,
            codigo,
            descricao,
            preco_ton,
            preco_sc,
            validade_tabela,
            fornecedor,
            'ATIVO',
            filhos,
            NOW(),
            NOW()
        FROM nao_cadastrados
        RETURNING id
        """
    )

    # Merge binds with existing params
    full_params = {**{"fornecedor": fornecedor, "lista": lista}, **binds}
    
    # Execute and fetch returned IDs
    res = db.execute(inserir_sql, full_params)
    new_ids = [row[0] for row in res.fetchall()]
    stats["inseridos"] = len(new_ids)

    # 4) Create Zeroed Tax Records for new products
    if new_ids:
        # Prepare bulk insert for taxes
        # We need to act quickly, so raw SQL is best. 
        # t_imposto_v2 columns: id (bigserial), produto_id, ipi, icms, iva_st, cbs, ibs, created_at, updated_at
        
        # We can construct a VALUES clause or use executemany via simple loop if safer.
        # But we can use SELECT UNNEST to be cleaner in one query.
        
        tax_sql = text("""
            INSERT INTO public.t_imposto_v2 (produto_id, ipi, icms, iva_st, cbs, ibs, created_at, updated_at)
            SELECT 
                pid, 
                0.00, 
                0.00, 
                0.00, 
                0.00, 
                0.00, 
                NOW(), 
                NOW()
            FROM unnest(:pids) AS pid
        """)
        
        # PostgreSQL unnest expects array, psycopg2 handles list as array.
        db.execute(tax_sql, {"pids": new_ids})

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
