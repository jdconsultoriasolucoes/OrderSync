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

print("Connecting to DB...")
with engine.connect() as conn:
    try:
        print("Attempting to add column reset_senha_obrigatorio to t_usuario...")
        conn.execute(text("ALTER TABLE t_usuario ADD COLUMN IF NOT EXISTS reset_senha_obrigatorio BOOLEAN DEFAULT FALSE;"))
        conn.commit()
        print("Column added successfully (or already existed).")
    except Exception as e:
        print(f"Error: {e}")
