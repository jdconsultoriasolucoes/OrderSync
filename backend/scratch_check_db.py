
import os
from sqlalchemy import create_engine, text

db_url = "postgresql://jdc:A2f2B5e6C2d9@dpg-cv20mptds78s73ba9gug-a.virginia-bethesda-dep.render.com/ordersync"
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check last 5 orders
    print("--- Last 5 orders ---")
    res = conn.execute(text("SELECT id_pedido, cliente, total_pedido, frete_total, usar_valor_com_frete FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 5"))
    for row in res:
        print(row)
    
    print("\n--- Items of the last order ---")
    last_id = conn.execute(text("SELECT id_pedido FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 1")).scalar()
    if last_id:
        res_items = conn.execute(text("SELECT id_item, codigo, preco_unit, preco_unit_frt, valor_frete_unitario, quantidade FROM tb_pedidos_itens WHERE id_pedido = :id"), {"id": last_id})
        for row in res_items:
            print(row)
