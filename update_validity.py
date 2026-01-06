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

with engine.connect() as conn:
    print("Updating Product Validity Dates to 2026-12-31...")
    
    # Update for all active products
    sql = text("UPDATE t_cadastro_produto_v2 SET validade_tabela = '2026-12-31' WHERE status_produto = 'ATIVO'")
    res = conn.execute(sql)
    print(f"Updated {res.rowcount} products.")
    
    conn.commit()
    print("Commit complete.")
