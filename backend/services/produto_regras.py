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
    res = db.execute(update_sql, {"fornecedor": fornecedor, "lista": lista})
    stats["atualizados"] = res.rowcount or 0

    # 1.1) Atualizar 'filhos' (ordem) para produtos que já existem
    update_filhos_sql = text(
        """
        WITH lista_ativa AS (
            SELECT codigo, filhos
            FROM public.t_preco_produto_pdf_v2
            WHERE ativo = TRUE
              AND fornecedor = :fornecedor
              AND lista = :lista
        )
        UPDATE public.t_cadastro_produto_v2 AS p
           SET filhos = la.filhos
        FROM lista_ativa AS la
        WHERE p.fornecedor   = :fornecedor
          AND p.tipo         = :lista
          AND p.codigo_supra = la.codigo
        """
    )
    db.execute(update_filhos_sql, {"fornecedor": fornecedor, "lista": lista})

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

    stats["inativados"] = res.rowcount or 0

    # -- Nova Lógica de ID Familia --
    # Verificar famílias novas na lista ativa que não têm correspondência na t_cadastro_produto_v2
    # ou que simplesmente ainda não têm ID definido (caso de produtos novos).
    # Na verdade, a regra é: Se vier uma família NO PDF que não existe no banco (pelo nome?), cria ID novo.
    # Mas familias são strings. 
    
    # 2.1 Identificar famílias distintas NA LISTA ATIVA
    familias_pdf = db.execute(text("""
        SELECT DISTINCT familia 
        FROM public.t_preco_produto_pdf_v2 
        WHERE ativo=TRUE AND fornecedor=:f AND lista=:l AND familia IS NOT NULL
    """), {"f": fornecedor, "l": lista}).fetchall()
    
    familias_nomes = [row[0] for row in familias_pdf]
    
    # Para cada família do PDF, verificar se já existe ID na t_cadastro_produto_v2
    # (busca glogalmente pelo nome da família, independente de fornecedor? 
    #  Geralmente familia é global, mas aqui parece vinculado a produto. 
    #  Vou assumir busca global pelo nome da familia na tabela de produtos).
    
    mapa_familia_id = {}
    
    # Burcar IDs existentes
    if familias_nomes:
        ftxt = text("SELECT DISTINCT familia, id_familia FROM public.t_cadastro_produto_v2 WHERE familia IN :fams AND id_familia IS NOT NULL")
        # bindparam não aceita lista direto as vezes no text puro sem expandir, mas o driver psycopg2 costuma aceitar tuple/list com IN
        # Vamos fazer um loop seguro ou tentar IN.
        # SQLAlchemy aceita IN :fams se passarmos tuple.
        existing_fams = db.execute(ftxt, {"fams": tuple(familias_nomes)}).fetchall()
        for f_nome, f_id in existing_fams:
            mapa_familia_id[f_nome] = f_id

    # Determinar MAX id atual
    max_id = db.execute(text("SELECT MAX(id_familia) FROM public.t_cadastro_produto_v2")).scalar() or 0
    
    # Atribuir IDs para as novas
    # Ordenar familias novas para manter consistência de atribuição
    familias_novas = [f for f in familias_nomes if f not in mapa_familia_id]
    familias_novas.sort() # Alfa order
    
    for f_novo in familias_novas:
        max_id += 10
        mapa_familia_id[f_novo] = max_id
        
    # Agora temos mapa_familia_id completo para o PDF atual.
    # Precisamos usar isso no INSERT. Como o INSERT é via SELECT, 
    # não dá pra injetar o mapa fácil no SQL puro massivo.
    # Solução: Criar tabela temporária ou atualizar a tabela PDF com o ID Familia calculado.
    
    # Vamos atualizar a t_preco_produto_pdf_v2 com o id_familia calculado para facilitar o insert
    # Primeiro adicionar coluna se não existir (mas é tabela fixa... não devo alterar schema dinamicamente em prod).
    # Melhor: Fazer o INSERT em loop ou:
    # 1. Criar tabela temporária de mapping (familia, id)
    # 2. Fazer Join no Insert.
    
    # Opção Simples: Update row-by-row na tabela PDF é lento? Não são tantas familias.
    # Mas a tabela PDF não tem coluna id_familia. E user não pediu pra criar nela.
    # User pediu pra criar no cadastro.
    
    # Vou usar CASE/WHEN gigante no INSERT? Pode quebrar se forem muitas familias.
    # Melhor: Criar tabela temporária (VALUES) na query.
    
    # Construction of VALUES list for joining
    # ('FAM A', 10), ('FAM B', 20)
    
    values_list = []
    for fam, fid in mapa_familia_id.items():
        # Escape single quotes in family name just in case (SQL injection risk avoided by using params usually, but constructing VALUES string needs care)
        # Vamos usar parametros numerados ou json.
        # Simplificação: Se familias forem poucas.
        pass
        
    # Create temp table logic via CTE
    # WITH map_fam(nome, id) AS (VALUES (:f1, :i1), (:f2, :i2)...)
    
    # Se lista for vazia, skip
    
    if mapa_familia_id:
        # Build params for CTE
        binds = {}
        values_parts = []
        for i, (fname, fid) in enumerate(mapa_familia_id.items()):
            pname = f"fn_{i}"
            pid = f"fid_{i}"
            binds[pname] = fname
            binds[pid] = fid
            values_parts.append(f"(:{pname}, :{pid})")
            
        cte_body = ", ".join(values_parts)
        
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
              ON  p.fornecedor   = la.fornecedor
              AND p.tipo         = la.lista
              AND p.codigo_supra = la.codigo
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
