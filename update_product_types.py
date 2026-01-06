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
    print("Starting Product Type Correction...")
    
    # 1. Update id_familia in V2 from V1 familia
    print("Step 1: Updating id_familia in t_cadastro_produto_v2 from t_cadastro_produto...")
    sql_update_familia = text("""
        UPDATE t_cadastro_produto_v2 v2
        SET id_familia = v1.familia
        FROM t_cadastro_produto v1
        WHERE v2.codigo_supra = v1.codigo_supra
          AND v1.familia IS NOT NULL
    """)
    res1 = conn.execute(sql_update_familia)
    print(f"Step 1 Complete. Rows updated: {res1.rowcount}")
    
    # 2. Update tipo in V2 from familia_produtos
    print("Step 2: Updating tipo in t_cadastro_produto_v2 from familia_produtos...")
    sql_update_tipo = text("""
        UPDATE t_cadastro_produto_v2 v2
        SET tipo = UPPER(fp.tipo) -- ensuring consistency
        FROM t_familia_produtos fp
        WHERE v2.id_familia = CAST(fp.id AS INTEGER)
          AND fp.tipo IS NOT NULL
    """)
    res2 = conn.execute(sql_update_tipo)
    print(f"Step 2 Complete. Rows updated: {res2.rowcount}")

    conn.commit()
    print("All updates committed.")
