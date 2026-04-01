import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

queries = [
    # 1. Vendas
    """
    SELECT 
        COALESCE(c.faturamento_municipio, c.entrega_municipio, 'Sem Município') as mun, 
        SUM(GREATEST(p.total_pedido - COALESCE(p.frete_total, 0), 0)) as total_valor,
        SUM(COALESCE(p.peso_total_kg, 0)) as total_peso
    FROM public.tb_pedidos p
    LEFT JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
    LIMIT 1
    """,
    # 2. Produtos
    """
    SELECT 
        i.nome, 
        SUM(i.quantidade) as qtd, 
        COALESCE(SUM(i.subtotal), 0) as fat,
        COALESCE(SUM(i.peso_liquido_total), 0) as peso
    FROM public.tb_pedidos_itens i
    JOIN public.tb_pedidos p ON i.id_pedido = p.id_pedido
    LIMIT 1
    """,
    # 3. Clientes
    """
    SELECT 
        p.cliente, 
        COALESCE(SUM(p.total_pedido), 0) as fat,
        COALESCE(SUM(p.peso_total_kg), 0) as peso
    FROM public.tb_pedidos p
    LIMIT 1
    """
]

with engine.connect() as conn:
    for i, q in enumerate(queries):
        print(f"--- Query {i+1} ---")
        try:
            res = conn.execute(text(q)).fetchall()
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
