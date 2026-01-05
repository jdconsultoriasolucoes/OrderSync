import os
from sqlalchemy import create_engine, inspect
import urllib.parse
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")

# Fallback string logic if env not loaded correctly contextually
if not DB_URL:
     # Hardcode Prod URL from summary for robustness
     DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)
inspector = inspect(engine)

print("--- Columns in t_cadastro_produto_v2 ---")
cols = inspector.get_columns("t_cadastro_produto_v2")
for c in cols:
    print(f"{c['name']} ({c['type']})")

print("\n--- Columns in t_imposto_v2 ---")
try:
    cols = inspector.get_columns("t_imposto_v2")
    for c in cols:
        print(f"{c['name']} ({c['type']})")
except:
    print("t_imposto_v2 not found")
