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
    print("--- Inspecting familia_produtos ---")
    try:
        res = conn.execute(text("SELECT * FROM familia_produtos LIMIT 1")).keys()
        print("Columns:", res)
        # Check actual content of 'tipo'
        rows = conn.execute(text("SELECT id, tipo FROM familia_produtos LIMIT 5")).fetchall()
        print("Sample Data:", rows)
    except Exception as e:
        print("Error reading familia_produtos:", e)

    print("\n--- Inspecting t_cadastro_produto (Legacy) ---")
    try:
        # Check 'familia' column content
        rows = conn.execute(text("SELECT codigo_supra, familia FROM t_cadastro_produto LIMIT 5")).fetchall()
        print("Sample Data:", rows)
    except Exception as e:
        print("Error reading t_cadastro_produto:", e)

    print("\n--- Inspecting t_cadastro_produto_v2 (Target) ---")
    try:
        # Check 'id_familia' column content
        rows = conn.execute(text("SELECT codigo_supra, id_familia, tipo FROM t_cadastro_produto_v2 LIMIT 5")).fetchall()
        print("Sample Data:", rows)
    except Exception as e:
        print("Error reading t_cadastro_produto_v2:", e)
