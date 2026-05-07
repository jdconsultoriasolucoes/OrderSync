import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

FIX_SQL = text("""
-- 1. Restaurar preços unitários dos itens do pedido 9707 a partir da tabela de produtos
UPDATE public.tb_pedidos_itens it
SET preco_unit = p.preco
FROM public.v_produto_v2_preco p
WHERE it.id_pedido = 9707
  AND it.codigo = p.codigo_supra::text
  AND (it.preco_unit IS NULL OR it.preco_unit = 0);

-- 2. Recalcular subtotal_sem_f e subtotal_com_f para o pedido 9707
UPDATE public.tb_pedidos_itens
SET 
    subtotal_sem_f = preco_unit * quantidade,
    preco_unit_frt = preco_unit + valor_frete_unitario,
    subtotal_com_f = (preco_unit + valor_frete_unitario) * quantidade
WHERE id_pedido = 9707;

-- 3. Recalcular totais no cabeçalho do pedido 9707
UPDATE public.tb_pedidos p
SET 
    total_sem_frete = (SELECT COALESCE(SUM(subtotal_sem_f), 0) FROM public.tb_pedidos_itens WHERE id_pedido = p.id_pedido),
    total_com_frete = (SELECT COALESCE(SUM(subtotal_com_f), 0) FROM public.tb_pedidos_itens WHERE id_pedido = p.id_pedido),
    frete_total = (SELECT COALESCE(SUM(valor_frete_unitario * quantidade), 0) FROM public.tb_pedidos_itens WHERE id_pedido = p.id_pedido),
    peso_total_kg = (SELECT COALESCE(SUM(peso_kg * quantidade), 0) FROM public.tb_pedidos_itens WHERE id_pedido = p.id_pedido)
WHERE id_pedido = 9707;

-- 4. Ajustar total_pedido final baseado na modalidade
UPDATE public.tb_pedidos
SET total_pedido = CASE WHEN usar_valor_com_frete THEN total_com_frete ELSE total_sem_frete END
WHERE id_pedido = 9707;
""")

with engine.connect() as conn:
    print("Fixing order 9707...")
    res = conn.execute(FIX_SQL)
    conn.commit()
    print("Done.")
