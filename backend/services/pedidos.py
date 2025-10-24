# services/pedidos.py
from sqlalchemy import text
from typing import Any, Dict, List, Tuple

LISTAGEM_SQL = text("""
SELECT
  a.id_pedido                               AS numero_pedido,
  a.created_at                              AS data_pedido,
  a.cliente                                 AS cliente_nome,
  a.codigo_cliente                          AS cliente_codigo,
  CASE WHEN a.usar_valor_com_frete THEN 'ENTREGA' ELSE 'RETIRADA' END AS modalidade,
  a.total_pedido                            AS valor_total,
  a.status                                  AS status_codigo,
  b.nome_tabela                             AS tabela_preco_nome,
  a.fornecedor                              AS fornecedor,
  a.link_url,
  a.link_status,
  (a.link_enviado_em IS NOT NULL)           AS link_enviado
FROM public.tb_pedidos a
JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
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
  a.cliente,
  a.contato_nome,
  a.contato_email,
  a.contato_fone,
  b.nome_tabela                  AS tabela_preco_nome,
  a.fornecedor,
  a.validade_ate,
  a.validade_dias,
  a.usar_valor_com_frete,
  a.peso_total_kg,
  a.frete_total,
  a.total_pedido,
  a.observacoes,
  a.status,
  a.confirmado_em,
  a.cancelado_em,
  a.cancelado_motivo,
  a.link_url,
  a.link_primeiro_acesso_em,
  a.link_status,
  a.created_at
FROM public.tb_pedidos a
JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
WHERE a.id_pedido = :id_pedido
""")

ITENS_JSON_SQL = text("""
SELECT COALESCE(
  jsonb_agg(
    jsonb_build_object(
      'codigo',      c.codigo,
      'nome',        c.nome,
      'embalagem',   c.embalagem,
      'quantidade',  c.quantidade,
      'preco_unit',  CASE WHEN a.usar_valor_com_frete THEN c.preco_unit_frt ELSE c.preco_unit END,
      'subtotal',    CASE WHEN a.usar_valor_com_frete THEN c.subtotal_com_f ELSE c.subtotal_sem_f END
    )
    ORDER BY c.id_item
  ),
  '[]'::jsonb
) AS itens
FROM public.tb_pedidos_itens c
JOIN public.tb_pedidos a ON a.id_pedido = c.id_pedido
WHERE c.id_pedido = :id_pedido
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
    atualizado_em = now()
WHERE id_pedido = :id_pedido
RETURNING id_pedido
""")

STATUS_EVENT_INSERT_SQL = text("""
INSERT INTO public.pedido_status_event (id, pedido_id, de_status, para_status, user_id, motivo, metadata, created_at)
VALUES (gen_random_uuid(), :pedido_id, :de_status, :para_status, :user_id, :motivo, :metadata::jsonb, now())
""")