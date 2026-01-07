import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)

def inspect_table():
    print("Inspecting t_preco_produto_pdf_v2...")
    with engine.connect() as conn:
        # Postgres query to get column details
        sql = text("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 't_preco_produto_pdf_v2'
        """)
        rows = conn.execute(sql).fetchall()
        for r in rows:
            print(f"{r.column_name}: {r.data_type} ({r.character_maximum_length})")

if __name__ == "__main__":
    inspect_table()
