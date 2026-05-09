
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://ordersync_db_user:E0P2m6x1I8v7mX9uE4V7s1A6i3U8v2@dpg-cuid6n9u0jms73ep37gg-a.oregon-postgres.render.com/ordersync_db?sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Adding frete_base_ton to tb_pedidos_itens...")
    try:
        conn.execute(text("ALTER TABLE public.tb_pedidos_itens ADD COLUMN frete_base_ton FLOAT DEFAULT 0.0"))
        conn.commit()
        print("Success.")
    except Exception as e:
        print(f"Error (maybe already exists): {e}")
    
    # Also add to tb_pedidos if we want to store a 'default' or just for consistency?
    # The user said 'diretamente na linha', so it's mainly for items.
    # But tb_pedidos has frete_kg, we can keep it as a legacy or default.
