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

def alter_schema():
    print("Altering t_preco_produto_pdf_v2 schema...")
    with engine.connect() as conn:
        with conn.begin():
            # Increase lista column size
            print("Altering 'lista' to VARCHAR(255)...")
            conn.execute(text("ALTER TABLE t_preco_produto_pdf_v2 ALTER COLUMN lista TYPE VARCHAR(255)"))
            
            # Increase codigo column size
            print("Altering 'codigo' to VARCHAR(255)...")
            conn.execute(text("ALTER TABLE t_preco_produto_pdf_v2 ALTER COLUMN codigo TYPE VARCHAR(255)"))
            
        print("Schema altered successfully.")

if __name__ == "__main__":
    alter_schema()
