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
    print("Checking View Data for IVA ST...")
    
    # Query the VIEW
    sql = text("""
        SELECT codigo_supra, nome_produto, tipo, iva_st 
        FROM v_produto_v2_preco 
        WHERE tipo = 'INSUMOS' AND iva_st > 0
        LIMIT 10
    """)
    rows = conn.execute(sql).mappings().all()
    
    if rows:
        print(f"Found {len(rows)} INSUMOS products with IVA ST > 0:")
        for r in rows:
            print(f"- {r['nome_produto']} (ST: {r['iva_st']})")
    else:
        print("No INSUMOS products found with IVA ST > 0.")
