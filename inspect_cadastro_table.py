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

def inspect_cadastro():
    print("Inspecting t_cadastro_produto_v2...")
    with engine.connect() as conn:
        # Check columns
        sql = text("""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 't_cadastro_produto_v2'
        """)
        rows = conn.execute(sql).fetchall()
        cols = [r.column_name for r in rows]
        print("Columns:", cols)
        
        # Check distinct values if potential columns exist
        potentials = ['tipo', 'grupo', 'lista', 'categoria']
        for p in potentials:
            if p in cols:
                print(f"Distinct {p}:", conn.execute(text(f"SELECT DISTINCT {p} FROM t_cadastro_produto_v2")).fetchall())

if __name__ == "__main__":
    inspect_cadastro()
