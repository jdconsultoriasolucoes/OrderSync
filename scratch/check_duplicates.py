import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

query = text("SELECT id_pedido, COUNT(*) FROM public.tb_pedidos GROUP BY id_pedido HAVING COUNT(*) > 1;")

with engine.connect() as conn:
    result = conn.execute(query)
    rows = result.fetchall()
    if not rows:
        print("No duplicate id_pedido found.")
    else:
        print(f"Found {len(rows)} duplicate id_pedido groups:")
        for r in rows:
            print(f"ID: {r[0]}, Count: {r[1]}")
