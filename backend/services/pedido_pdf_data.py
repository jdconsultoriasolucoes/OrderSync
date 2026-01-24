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

            CASE
                WHEN c.nome_fantasia IS NULL
                OR c.nome_fantasia = 'nan'
                OR c.nome_fantasia = ''
                THEN 'Sem Nome Fantasia'
                ELSE c.nome_fantasia
            END AS nome_fantasia,

            t.frete_kg AS frete_kg,

            p.confirmado_em,
            p.data_retirada,
            p.frete_total,
            p.peso_total_kg, /* Este costuma ser o peso considerado para frete (agora bruto) */
            p.total_pedido,
            p.observacoes,

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
        LEFT JOIN public.t_cadastro_cliente c
            ON c.codigo::text = p.codigo_cliente

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
        LEFT JOIN t_cadastro_produto_v2 prod
            ON prod.codigo_supra = i.codigo
            AND prod.fornecedor = tp.fornecedor

        WHERE p.id_pedido = :pid
        ORDER BY i.quantidade DESC, i.id_item;
    """)

    rows = db.execute(sql, {"pid": pedido_id}).mappings().all()
    if not rows:
        raise ValueError("Pedido não encontrado")

    head = rows[0]

    itens = []
    
    # Recalcula pesos
    sum_peso_liq = 0.0
    sum_peso_bru = 0.0

    for r in rows:
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

    return PedidoPdf(
        id_pedido=head["id_pedido"],
        codigo_cliente=head["codigo_cliente"],
        cliente=head["cliente"] or "",
        nome_fantasia=head.get("nome_fantasia") or "Sem Nome Fantasia",
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
