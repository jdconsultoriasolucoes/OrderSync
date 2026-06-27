import os
from sqlalchemy import create_engine, text
import json

db_url = "postgresql://jdc:A2f2B5e6C2d9@dpg-cv20mptds78s73ba9gug-a.virginia-bethesda-dep.render.com/ordersync"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- Pedidos possivelmente incorretos (usar_valor_com_frete = TRUE mas frete_total = 0) ---")
    query = text("""
        SELECT id_pedido, cliente, total_pedido, frete_total, usar_valor_com_frete, created_at, atualizado_em
        FROM tb_pedidos 
        WHERE usar_valor_com_frete = TRUE 
          AND (frete_total IS NULL OR frete_total <= 0)
        ORDER BY id_pedido DESC
    """)
    res = conn.execute(query).fetchall()
    
    print(f"Total encontrados: {len(res)}")
    for row in res[:20]: # show first 20
        # Convert row to dict for easier printing if datetime is present
        print(dict(row._mapping))
