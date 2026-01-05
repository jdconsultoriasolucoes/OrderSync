import os
from sqlalchemy import create_engine, text

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)

print("-- PROD CLIENT DATA CHECK --")
with engine.connect() as conn:
    # Check V1 table
    try:
        v1_count = conn.execute(text("SELECT COUNT(*) FROM t_cadastro_cliente")).scalar()
        print(f"t_cadastro_cliente (V1): {v1_count} rows")
    except Exception as e:
        print(f"t_cadastro_cliente (V1): Not found or error: {e}")

    # Check V2 table again
    v2_count = conn.execute(text("SELECT COUNT(*) FROM t_cadastro_cliente_v2")).scalar()
    print(f"t_cadastro_cliente_v2 (V2): {v2_count} rows")
