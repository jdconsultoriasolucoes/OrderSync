import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    order_count = conn.execute(text("SELECT COUNT(*) FROM public.tb_pedidos")).scalar()
    item_count = conn.execute(text("SELECT COUNT(*) FROM public.tb_pedidos_itens")).scalar()
    duplicates = conn.execute(text("SELECT id_pedido, COUNT(*) FROM public.tb_pedidos GROUP BY id_pedido HAVING COUNT(*) > 1")).fetchall()
    manual_freight_col = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tb_pedidos_itens' AND column_name='manual_freight'")).scalar()

    print(f"Orders: {order_count}")
    print(f"Items: {item_count}")
    print(f"Duplicate IDs: {len(duplicates)}")
    print(f"Manual Freight Col Exists: {bool(manual_freight_col)}")
