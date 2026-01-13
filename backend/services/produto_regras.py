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

    # Identificar famílias distintas NA LISTA ATIVA
    familias_pdf = db.execute(text("""
        SELECT DISTINCT familia 
        FROM public.t_preco_produto_pdf_v2 
        WHERE ativo=TRUE AND fornecedor=:f AND lista=:l AND familia IS NOT NULL
    """), {"f": fornecedor, "l": lista}).fetchall()
    
    familias_nomes = [row[0] for row in familias_pdf]
    mapa_familia_id = {}
    
    # 1. Buscar IDs já existentes na tabela t_familia_produtos
    if familias_nomes:
        # Busca por familia (nome "cru" do PDF - antigo familia_carga)
        ftxt = text("SELECT familia, id FROM public.t_familia_produtos WHERE tipo=:tipo AND familia IN :fams")
        existing_fams = db.execute(ftxt, {"tipo": lista, "fams": tuple(familias_nomes)}).fetchall()
        for f_nome, f_id in existing_fams:
            mapa_familia_id[f_nome] = f_id

    # 2. Identificar novas familias que precisam ser criadas
    familias_novas = [f for f in familias_nomes if f not in mapa_familia_id]
    familias_novas.sort()
    
    if familias_novas:
        # Determinar MAX id atual na tabela t_familia_produtos para esse TIPO
        max_id = db.execute(
            text("SELECT MAX(id) FROM public.t_familia_produtos WHERE tipo = :lista"),
            {"lista": lista}
        ).scalar() or 0
        
        # Inserir as novas famílias
        # Preenche familia (raw) e marca (clean) com o mesmo valor inicial
        for f_novo in familias_novas:
            max_id += 10
            # Insert into t_familia_produtos explicitly
            db.execute(
                text("INSERT INTO public.t_familia_produtos (id, tipo, familia, marca) VALUES (:id, :tipo, :fam, :marca)"),
                {"id": max_id, "tipo": lista, "fam": f_novo, "marca": f_novo}
            )
            mapa_familia_id[f_novo] = max_id
        
        # db.commit() -> Removed to keep transaction atomic (will commit at end of func)
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
        WITH map_fam(nome_fam_raw, id_fam) AS (
            VALUES {cte_body}
        ),
        # Agora JOIN no map_fam é via familia (raw)
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
            LEFT JOIN map_fam m ON m.nome_fam_raw = l.familia
            WHERE l.ativo = TRUE
              AND l.fornecedor = :fornecedor
              AND l.lista = :lista
        ),
        # JOIN map_fam.nome_fam_raw = l.familia
        # Recuperamos o `id_fam`
        lista_ativa_com_id AS (
           SELECT la.*, m.id_fam 
           FROM lista_ativa la
           LEFT JOIN map_fam m ON m.nome_fam_raw = la.familia
        ),
        # Recuperar o nome oficial da familia (coluna 'marca') da tabela t_familia_produtos
        matches AS (
             SELECT DISTINCT ON (la.codigo)
                p.id,
                la.*,
                fp.marca as marca_oficial
             FROM lista_ativa_com_id la
             LEFT JOIN public.t_familia_produtos fp ON fp.id = la.id_fam
             JOIN public.t_cadastro_produto_v2 p
               ON TRIM(p.tipo) = la.lista
               AND TRIM(p.codigo_supra) = la.codigo
               AND (
                 p.fornecedor = la.fornecedor
                 OR p.fornecedor IS NULL
                 OR p.fornecedor = ''
                 OR p.fornecedor ILIKE '%' || la.fornecedor || '%'
               )
             ORDER BY 
                la.codigo, 
                -- Priority: Exact Match > Partial > Null > ID Desc
                CASE WHEN p.fornecedor = la.fornecedor THEN 1 
                     WHEN p.fornecedor ILIKE '%' || la.fornecedor || '%' THEN 2
                     ELSE 3 END ASC,
                p.id DESC
        )
        UPDATE public.t_cadastro_produto_v2 AS p
           SET preco_anterior          = p.preco,
               preco_tonelada_anterior = p.preco_tonelada,
               preco                   = m.preco_sc,
               preco_tonelada          = m.preco_ton,
               validade_tabela         = m.validade_tabela,
               familia                 = m.familia, -- familia recebe o valor RAW do PDF
               marca                   = COALESCE(m.marca_oficial, m.familia), -- marca recebe o valor CLEAN (ou RAW se nula)
               fornecedor              = m.fornecedor,
               filhos                  = m.filhos,
               status_produto          = 'ATIVO',
               id_familia              = COALESCE(p.id_familia, m.id_fam)
        FROM matches AS m
        WHERE p.id = m.id
        """
    )
    
    # Merge params
    run_params = {**{"fornecedor": fornecedor, "lista": lista}, **binds}
    res = db.execute(update_sql, run_params)
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

    # 3) Inserir produtos novos
    inserir_sql = text(
        f"""
        WITH map_fam(nome_fam_carga, id_fam) AS (
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
            LEFT JOIN map_fam m ON m.nome_fam_carga = l.familia
            WHERE l.ativo = TRUE
              AND l.fornecedor = :fornecedor
              AND l.lista = :lista
        ),
        # JOIN map_fam on familia_carga
        lista_ativa_com_id AS (
           SELECT la.*, m.id_fam
           FROM lista_ativa la
           LEFT JOIN map_fam m ON m.nome_fam_carga = la.familia
        ),
        # JOIN t_familia_produtos para pegar nome oficial
        nao_cadastrados AS (
            SELECT 
                la.*,
                fp.familia as familia_oficial
            FROM lista_ativa_com_id la
            LEFT JOIN public.t_familia_produtos fp ON fp.id = la.id_fam
            LEFT JOIN public.t_cadastro_produto_v2 p
              ON  TRIM(p.tipo) = la.lista
              AND TRIM(p.codigo_supra) = la.codigo
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
        SELECT DISTINCT ON (codigo)
            lista,
            COALESCE(familia_oficial, familia),
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
        ON CONFLICT (fornecedor, tipo, codigo_supra) DO NOTHING
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
