import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")

if not DB_URL:
    # Fallback to the one seen in migrate_clients_data.py if env not loaded
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("Searching for Gabriela...")
    sql = text("""
        SELECT id, cadastro_nome_cliente, cadastro_tipo_cliente, cadastro_codigo_da_empresa
        FROM t_cadastro_cliente_v2
        WHERE cadastro_nome_cliente ILIKE :name
    """)
    result = conn.execute(sql, {"name": "%Gabriela%Araujo%"}).mappings().all()
    
    if not result:
        print("No client found.")
    else:
        for row in result:
            print(f"ID: {row['id']}")
            print(f"Nome: {row['cadastro_nome_cliente']}")
            print(f"Tipo Cliente: '{row['cadastro_tipo_cliente']}'")
            print(f"Codigo: {row['cadastro_codigo_da_empresa']}")
            print("-" * 20)
