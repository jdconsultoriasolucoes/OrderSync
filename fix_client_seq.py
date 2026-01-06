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
    print("Fixing Sequence for t_cadastro_cliente_v2...")
    
    # 1. Get Max ID
    res = conn.execute(text("SELECT MAX(id) FROM t_cadastro_cliente_v2")).scalar()
    max_id = res if res is not None else 0
    print(f"Current Max ID in table: {max_id}")
    
    # 2. Reset Sequence
    # setval('seq', val) sets the current value. The next nextval() will return val + 1.
    sql_reset = text(f"SELECT setval('cliente_v2_id_seq', {max_id})")
    conn.execute(sql_reset)
    
    print(f"Sequence 'cliente_v2_id_seq' reset to {max_id}. Next ID will be {max_id + 1}.")
    conn.commit()
