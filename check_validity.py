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
    print("Checking Product Validity Dates...")
    sql = text("SELECT MAX(CAST(validade_tabela AS DATE)) FROM t_cadastro_produto_v2 WHERE status_produto = 'ATIVO'")
    max_date = conn.execute(sql).scalar()
    print(f"Max Validade Tabela (ATIVO): {max_date}")
    
    # Also check sample values
    print("Sample values:")
    rows = conn.execute(text("SELECT codigo_supra, validade_tabela FROM t_cadastro_produto_v2 WHERE status_produto = 'ATIVO' LIMIT 5")).fetchall()
    for r in rows:
        print(r)
