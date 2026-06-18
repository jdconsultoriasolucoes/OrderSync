# services/pedidos.py
from sqlalchemy import text
from typing import Any, Dict, List, Tuple

LISTAGEM_SQL = text("""
SELECT
  a.id_pedido                               AS numero_pedido,
  a.created_at                              AS data_pedido,
  COALESCE(c.cadastro_nome_cliente, a.cliente) AS cliente_nome,
  a.codigo_cliente                          AS cliente_codigo,
  CASE WHEN a.usar_valor_com_frete THEN 'ENTREGA' ELSE 'RETIRADA' END AS modalidade,
  a.total_pedido                            AS valor_total,
  a.status                                  AS status_codigo,
  COALESCE(b.nome_tabela, 'DEBUG-NULL')     AS tabela_preco_nome,
  a.fornecedor                              AS fornecedor,
  a.link_url,
  a.link_status,
  (a.link_enviado_em IS NOT NULL)           AS link_enviado,
  COALESCE(a.peso_total_kg, 0)              AS peso_total,
  c.entrega_municipio                      AS municipio,
  c.entrega_rota_principal                 AS rota_principal
FROM public.tb_pedidos a
JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
LEFT JOIN public.t_cadastro_cliente_v2 c 
  ON c.cadastro_codigo_da_empresa::text = a.codigo_cliente 
  AND a.codigo_cliente != ''
WHERE a.created_at >= :from
  AND a.created_at <  :to
  AND (:status_list::text[] IS NULL OR a.status = ANY(:status_list))
  AND (:tabela_nome  IS NULL OR b.nome_tabela ILIKE :tabela_nome)
  AND (:cliente_busca IS NULL OR (a.cliente ILIKE :cliente_busca OR a.codigo_cliente ILIKE :cliente_busca))
  AND (:fornecedor_busca IS NULL OR a.fornecedor ILIKE :fornecedor_busca)
ORDER BY a.created_at DESC, a.id_pedido DESC
LIMIT :limit OFFSET :offset
""")

COUNT_SQL = text("""
SELECT COUNT(*) AS total
FROM public.tb_pedidos a
JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
WHERE a.created_at >= :from
  AND a.created_at <  :to
  AND (:status_list::text[] IS NULL OR a.status = ANY(:status_list))
  AND (:tabela_nome  IS NULL OR b.nome_tabela ILIKE :tabela_nome)
  AND (:cliente_busca IS NULL OR (a.cliente ILIKE :cliente_busca OR a.codigo_cliente ILIKE :cliente_busca))
  AND (:fornecedor_busca IS NULL OR a.fornecedor ILIKE :fornecedor_busca)
""")

RESUMO_SQL = text("""
SELECT
  a.id_pedido,
  a.codigo_cliente,
  COALESCE(c.cadastro_nome_cliente, a.cliente) AS cliente,
  COALESCE(a.contato_nome, c.compras_nome_responsavel) AS contato_nome,
  COALESCE(a.contato_email, c.compras_email_resposavel) AS contato_email,
  COALESCE(a.contato_fone, c.compras_celular_responsavel) AS contato_fone,
  c.compras_telefone_fixo_responsavel AS cliente_telefone,
  c.compras_celular_responsavel AS cliente_celular,
  COALESCE(a.tabela_preco_nome, b.nome_tabela) AS tabela_preco_nome,
  COALESCE(
    CASE
      WHEN c.cadastro_nome_fantasia IS NULL OR c.cadastro_nome_fantasia IN ('nan', '') THEN 'Sem Nome Fantasia'
      ELSE c.cadastro_nome_fantasia
    END,
    'Sem Nome Fantasia'
  ) AS nome_fantasia,
  a.fornecedor,
  a.validade_ate,
  a.validade_dias,
  a.usar_valor_com_frete,
  a.peso_total_kg,
  a.frete_total,
  a.frete_kg,
  a.total_pedido,
  a.valor_ajuste,
  a.observacoes,
  a.status,
  a.confirmado_em,
  a.cancelado_em,
  a.cancelado_motivo,
  a.link_url,
  a.link_primeiro_acesso_em,
  a.link_status,
  a.pedido_supra,
  a.nota_fiscal,
  a.created_at,
  a.calcula_st,
  cg.numero_carga AS numero_carga
FROM public.tb_pedidos a
LEFT JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
LEFT JOIN public.t_cadastro_cliente_v2 c 
  ON c.cadastro_codigo_da_empresa::text = a.codigo_cliente
  AND a.codigo_cliente != ''
LEFT JOIN (
    SELECT cp.numero_pedido, cr.numero_carga
    FROM public.tb_cargas_pedidos cp
    JOIN public.tb_cargas cr ON cr.id = cp.id_carga
) cg ON cg.numero_pedido::text = a.id_pedido::text
WHERE a.id_pedido = :id_pedido
""")

ITENS_JSON_SQL = text("""
SELECT COALESCE(
  jsonb_agg(
    jsonb_build_object(
      'codigo',             c.codigo,
      'nome',               c.nome,
      'embalagem',          c.embalagem,
      'quantidade',         c.quantidade,
      'preco_unit',         c.preco_unit,
      'preco_unit_frt',     c.preco_unit_frt,
      'subtotal_sem_f',     c.subtotal_sem_f,
      'subtotal_com_f',     c.subtotal_com_f,
      'condicao_pagamento', c.condicao_pagamento,
      'tabela_comissao',    c.tabela_comissao,
      'manual_freight',     COALESCE(c.manual_freight, FALSE),
      'valor_frete_unitario', COALESCE(c.valor_frete_unitario, 0),
      'markup',             COALESCE(c.markup, 0),
      'valor_final_markup',  COALESCE(c.valor_final_markup, 0),
      'valor_s_frete_markup', COALESCE(c.valor_s_frete_markup, 0),
      'frete_base_ton',      COALESCE(c.frete_base_ton, 0),
      'peso_liquido_unit',  COALESCE(c.peso_kg, prod.peso, 0),
      'peso_liquido_total', ROUND(COALESCE(c.peso_kg, prod.peso, 0) * c.quantidade, 3)
    )
    ORDER BY c.id_item
  ),
  '[]'::jsonb
) AS itens
FROM public.tb_pedidos_itens c
JOIN public.tb_pedidos a ON a.id_pedido = c.id_pedido
LEFT JOIN (
  SELECT codigo_supra, MAX(peso) as peso
  FROM public.t_cadastro_produto_v2
  GROUP BY codigo_supra
) prod ON prod.codigo_supra = c.codigo
WHERE c.id_pedido = :id_pedido
  AND c.quantidade > 0
""")


STATUS_SQL = text("""
SELECT codigo, rotulo, cor_hex, ordem, ativo
FROM public.pedido_status
WHERE ativo IS DISTINCT FROM FALSE
ORDER BY COALESCE(ordem, 999), codigo
""")

STATUS_UPDATE_SQL = text("""
UPDATE public.tb_pedidos
SET status = :para_status,
    atualizado_em = now(),
    atualizado_por = :user_id
WHERE id_pedido = :id_pedido
RETURNING id_pedido
""")

STATUS_EVENT_INSERT_SQL = text("""
INSERT INTO public.pedido_status_event (id, pedido_id, de_status, para_status, user_id, motivo, metadata, created_at)
VALUES (gen_random_uuid(), :pedido_id, :de_status, :para_status, :user_id, :motivo, CAST(:metadata AS jsonb), now())
""")
