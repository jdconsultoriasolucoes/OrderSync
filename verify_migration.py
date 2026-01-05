
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
    try:
        # Total rows
        result = conn.execute(text("SELECT COUNT(*) FROM t_cadastro_cliente_v2"))
        total = result.scalar()
        
        # Rows with tipo_pessoa populated
        result = conn.execute(text("SELECT COUNT(*) FROM t_cadastro_cliente_v2 WHERE tipo_pessoa IS NOT NULL"))
        populated = result.scalar()
        
        print(f"Total rows: {total}")
        print(f"Populated rows: {populated}")
        
        # Sample
        result = conn.execute(text("SELECT cadastro_nome_cliente, tipo_pessoa FROM t_cadastro_cliente_v2 LIMIT 5"))
        print("\nSample:")
        for row in result:
            print(row)
            
    except Exception as e:
        print(f"Error: {e}")
