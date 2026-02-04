# services/pedido_pdf_data.py
from sqlalchemy import text
from database import SessionLocal
from models.pedido_pdf import PedidoPdf, PedidoPdfItem
from datetime import timedelta


def carregar_pedido_pdf(db, pedido_id: int) -> PedidoPdf:
    sql = text("""
        SELECT
            p.id_pedido,
            p.codigo_cliente,
            p.cliente,
            c.cadastro_nome_cliente AS nome_empresarial, /* RAZAO SOCIAL LEGAL V2 */

            CASE
                WHEN c.cadastro_nome_fantasia IS NULL
                OR c.cadastro_nome_fantasia = 'nan'
                OR c.cadastro_nome_fantasia = ''
                THEN 'Sem Nome Fantasia'
                ELSE c.cadastro_nome_fantasia
            END AS nome_fantasia,

            t.frete_kg AS frete_kg,

            p.confirmado_em,
            p.data_retirada,
            p.frete_total,
            p.peso_total_kg, /* Este costuma ser o peso considerado para frete (agora bruto) */
            p.total_pedido,
            p.observacoes,
            
            i.id_item, /* REQUIRED FOR DEDUPLICATION */
            i.codigo              AS item_codigo,
            i.nome                AS item_nome,
            i.embalagem           AS item_embalagem,
            i.quantidade          AS item_quantidade,
            i.condicao_pagamento  AS item_condicao_pagamento,
            i.tabela_comissao     AS item_tabela_comissao,
            i.preco_unit          AS item_preco_retira,
            i.preco_unit_frt      AS item_preco_entrega,
            
            prod.peso             AS item_peso_liquido_cad,
            prod.peso_bruto       AS item_peso_bruto_cad,
            tp.fornecedor         AS item_fornecedor,

            tp.markup                 AS item_markup,
            tp.valor_final_markup     AS item_valor_final_markup,
            tp.valor_s_frete_markup   AS item_valor_s_frete_markup

        FROM tb_pedidos p
        LEFT JOIN public.t_cadastro_cliente_v2 c
            ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente

        -- AQUI o pulo do gato: "condensa" a tabela de preço em 1 linha por tabela
        LEFT JOIN (
            SELECT
                id_tabela,
                MAX(frete_kg) AS frete_kg
            FROM tb_tabela_preco
            GROUP BY id_tabela
        ) t
            ON t.id_tabela = p.tabela_preco_id

        JOIN tb_pedidos_itens i
            ON i.id_pedido = p.id_pedido
            
        -- Join para pegar dados de markup originais da tabela de preço
        LEFT JOIN tb_tabela_preco tp
            ON tp.id_tabela = p.tabela_preco_id 
            AND tp.codigo_produto_supra = i.codigo
            AND tp.ativo = TRUE

        -- Busca produto usando o fornecedor da tabela de preço para evitar duplicidade
        -- FIX: Usar subquery para garantir 1 linha por código e evitar 0kg se fornecedor divergir
        LEFT JOIN (
            SELECT 
                codigo_supra, 
                MAX(peso) as peso, 
                MAX(peso_bruto) as peso_bruto 
            FROM t_cadastro_produto_v2 
            GROUP BY codigo_supra
        ) prod
            ON prod.codigo_supra = i.codigo

        WHERE p.id_pedido = :pid
        ORDER BY i.quantidade DESC, i.id_item;
    """)

    rows = db.execute(sql, {"pid": pedido_id}).mappings().all()
    if not rows:
        raise ValueError("Pedido não encontrado")

    head = rows[0]

    itens = []
    seen_items = set() # Track processed items
    
    # Recalcula pesos
    sum_peso_liq = 0.0
    sum_peso_bru = 0.0

    for r in rows:
        # DEDUPLICATION CHECK
        item_id = r["id_item"]
        if item_id in seen_items:
            continue
        seen_items.add(item_id)

        qtd = float(r["item_quantidade"] or 0)
        
        # Pesos unitários
        p_liq = float(r["item_peso_liquido_cad"] or 0)
        p_bru = float(r["item_peso_bruto_cad"] or 0)
        
        # Fallback se peso bruto for 0, usa liquido
        if p_bru <= 0: p_bru = p_liq

        sum_peso_liq += p_liq * qtd
        sum_peso_bru += p_bru * qtd

        itens.append(PedidoPdfItem(
            codigo=str(r["item_codigo"] or ""),
            produto=r["item_nome"] or "",
            embalagem=r["item_embalagem"],
            quantidade=qtd,
            condicao_pagamento=r.get("item_condicao_pagamento"),
            tabela_comissao=r.get("item_tabela_comissao"),
            valor_retira=float(r["item_preco_retira"] or 0),
            valor_entrega=float(r["item_preco_entrega"] or 0),
            markup=float(r["item_markup"] or 0),
            valor_final_markup=float(r["item_valor_final_markup"] or 0),
            valor_s_frete_markup=float(r["item_valor_s_frete_markup"] or 0),
            fornecedor=r.get("item_fornecedor") or "",
        ))

    # PREFER V2 CODE IF AVAILABLE
    # Se p.codigo_cliente for "Não cadastrado" ou null, e achamos match em c.codigo, usamos c.codigo
    cod_final = head["codigo_cliente"]
    # Se existe codigo da empresa na query (V2), vamos usar?
    # O SQL acima nao seleciona c.cadastro_codigo_da_empresa explicitamente no SELECT list.
    # Precisamos adicionar no SELECT lá de cima.
    # Mas como não posso editar o SELECT list e o JOIN juntos facilmente sem reescrever tudo...
    # Vou editar o SELECT list primeiro em outro passo ou assumir que vou reescrever o bloco todo.
    # O replacement atual JÁ inclui o bloco todo.
    # Vou ajustar o SELECT list aqui no replacement content.

    # ... [See logic below in actual tool call] ...
    # Wait, I need to verify I'm editing the whole function or block.
    # The snippet covers from FROM tb_pedidos to return.
    # But I missed the SELECT list at the top.
    # Lines 8-148 cover pretty much the whole function.
    # I should start the replacement at line 51 (FROM) and go down.
    # But I also need to change the SELECT to get the V2 code.
    
    # Let's perform TWO replacements or replace the WHOLE function 
    # to be safe and clean. 
    # Logic:
    # 1. Update SELECT to include `c.cadastro_codigo_da_empresa`
    # 2. Update LEFT JOIN Logic
    # 3. Update return logic to use V2 code if better.
    return PedidoPdf(
        id_pedido=head["id_pedido"],
        codigo_cliente=head["codigo_cliente"], # Will fix this in next step
        cliente=head["cliente"] or "",
        nome_fantasia=head.get("nome_fantasia") or "Sem Nome Fantasia",
        razao_social=head.get("nome_empresarial") or None,
        data_pedido=head["confirmado_em"],
        data_entrega_ou_retirada=head["data_retirada"],
        frete_total=float(head["frete_total"] or 0),
        frete_kg=float(head.get("frete_kg") or 0),
        validade_tabela="Não se aplica",
        total_peso_bruto=sum_peso_bru,
        total_peso_liquido=sum_peso_liq,
        total_valor=float(head["total_pedido"] or 0),
        observacoes=(head.get("observacoes") or ""),
        itens=itens,
    )
