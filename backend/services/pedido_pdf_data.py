# services/pedido_pdf_data.py
from sqlalchemy import text
from database import SessionLocal
from models.pedido_pdf import PedidoPdf, PedidoPdfItem

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
            p.confirmado_em,
            p.data_retirada,
            p.frete_total,
            p.peso_total_kg,
            p.total_pedido,
            p.observacoes,
            i.codigo              AS item_codigo,
            i.nome                AS item_nome,
            i.embalagem           AS item_embalagem,
            i.quantidade          AS item_quantidade,
            i.condicao_pagamento  AS item_condicao_pagamento,
            i.tabela_comissao     AS item_tabela_comissao,
            i.preco_unit          AS item_preco_retira,
            i.preco_unit_frt      AS item_preco_entrega
        FROM tb_pedidos p
        LEFT JOIN public.t_cadastro_cliente c
               ON c.codigo::text = p.codigo_cliente
        JOIN tb_pedidos_itens i
          ON i.id_pedido = p.id_pedido
        WHERE p.id_pedido = :pid
        ORDER BY i.id_item
    """)

    rows = db.execute(sql, {"pid": pedido_id}).mappings().all()
    if not rows:
        raise ValueError("Pedido não encontrado")

    head = rows[0]

    itens = []
    for r in rows:
        itens.append(PedidoPdfItem(
            codigo=str(r["item_codigo"] or ""),
            produto=r["item_nome"] or "",
            embalagem=r["item_embalagem"],
            quantidade=float(r["item_quantidade"] or 0),
            condicao_pagamento=r.get("item_condicao_pagamento"),
            tabela_comissao=r.get("item_tabela_comissao"),
            valor_retira=float(r["item_preco_retira"] or 0),
            valor_entrega=float(r["item_preco_entrega"] or 0),
        ))

    return PedidoPdf(
        id_pedido=head["id_pedido"],
        codigo_cliente=head["codigo_cliente"],
        cliente=head["cliente"] or "",
        nome_fantasia=head.get("nome_fantasia") or "Sem Nome Fantasia",
        data_pedido=head["confirmado_em"],
        data_entrega_ou_retirada=head["data_retirada"],
        frete_total=float(head["frete_total"] or 0),
        total_peso_bruto=float(head["peso_total_kg"] or 0),
        total_valor=float(head["total_pedido"] or 0),
        observacoes=(head.get("observacoes") or ""),
        itens=itens,
    )