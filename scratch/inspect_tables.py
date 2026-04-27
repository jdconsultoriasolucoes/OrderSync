import os
import sys
from sqlalchemy import text
# Add backend to path to import database
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "backend")))
from database import engine

def inspect_table(table_name):
    print(f"--- Schema for {table_name} ---")
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"))
        for row in res:
            print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    inspect_table("tb_pedidos")
    inspect_table("tb_pedidos_itens")
