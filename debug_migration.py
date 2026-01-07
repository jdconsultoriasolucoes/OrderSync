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

def debug_keys():
    print("Connecting...")
    with engine.connect() as conn:
        print("Fetching one row...")
        row = conn.execute(text("SELECT * FROM ingestao_produto LIMIT 1")).mappings().first()
        if row:
            print("Keys found:", list(row.keys()))
        else:
            print("No rows found.")
        
        # Test update one row
        if row:
            key = row.get("codigo_supra")
            if key:
                print(f"Attempting to update key: {key}")
                sql = text("UPDATE t_cadastro_produto_v2 SET updated_at = NOW() WHERE codigo_supra = :key")
                res = conn.execute(sql, {"key": key})
                conn.commit()
                print(f"Update test result: {res.rowcount} rows affected.")
            else:
                print("codigo_supra key not found in row.")

if __name__ == "__main__":
    debug_keys()
