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
    print("Checking Product Types and IVA ST...")
    
    # Check distinct types
    sql_types = text("SELECT DISTINCT tipo FROM t_cadastro_produto_v2")
    types = conn.execute(sql_types).fetchall()
    print("Product Types found:", [row[0] for row in types])

    # Check some products with IVA_ST
    sql_prods = text("SELECT codigo_supra, nome_produto, tipo, iva_st FROM t_cadastro_produto_v2 LIMIT 20")
    prods = conn.execute(sql_prods).mappings().all()
    
    print("\nSample Products:")
    for p in prods:
        print(f"Code: {p['codigo_supra']} | Name: {p['nome_produto']} | Type: {p['tipo']} | IVA_ST: {p['iva_st']}")

