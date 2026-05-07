import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

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
      'peso_liquido_unit',  COALESCE(c.peso_kg, prod.peso, 0),
      'peso_liquido_total', ROUND(COALESCE(c.peso_kg, prod.peso, 0) * c.quantidade, 3)
    )
    ORDER BY c.id_item
  ),
  '[]'::jsonb
) AS itens
FROM public.tb_pedidos_itens c
LEFT JOIN (
  SELECT codigo_supra, MAX(peso) as peso
  FROM public.t_cadastro_produto_v2
  GROUP BY codigo_supra
) prod ON prod.codigo_supra = c.codigo
WHERE c.id_pedido = :id_pedido
""")

with engine.connect() as conn:
    print("Checking JSON for order 9707 items:")
    res = conn.execute(ITENS_JSON_SQL, {"id_pedido": 9707}).scalar()
    print(json.dumps(res, indent=2))
