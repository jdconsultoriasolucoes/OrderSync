import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Use the logic from existing files to get DB URL
load_dotenv(r"e:\OrderSync\.env")
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)

def inspect_columns(table_name):
    print(f"--- Columns for {table_name} ---")
    with engine.connect() as conn:
        try:
            result = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"))
            cols = result.fetchall()
            for c in cols:
                print(f"{c[0]} ({c[1]})")
            if not cols:
                print("No columns found (table might not exist or wrong name).")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    inspect_columns("ingestao_produto")
    inspect_columns("t_cadastro_produto_v2")
