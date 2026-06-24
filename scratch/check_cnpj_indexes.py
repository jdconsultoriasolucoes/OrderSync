import os
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("=== INDEXES ON t_cadastro_cliente_v2 ===")
        res = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 't_cadastro_cliente_v2'
        """))
        for row in res:
            print(f"Index: {row[0]}\nDefinition: {row[1]}\n")

        print("=== CONSTRAINTS ON t_cadastro_cliente_v2 ===")
        res_const = conn.execute(text("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'public.t_cadastro_cliente_v2'::regclass
        """))
        for row in res_const:
            print(f"Constraint: {row[0]}\nDefinition: {row[1]}\n")

except Exception as e:
    print(f"Error: {e}")
