import os
from sqlalchemy import create_engine, text

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)

print("-- INSPECTING ID COLUMN --")
with engine.connect() as conn:
    # Postgres specific query to check default value/sequence
    sql = """
    SELECT column_name, data_type, column_default, is_nullable
    FROM information_schema.columns
    WHERE table_name = 't_cadastro_cliente_v2' AND column_name = 'id';
    """
    result = conn.execute(text(sql)).fetchone()
    print(f"Details: {result}")
