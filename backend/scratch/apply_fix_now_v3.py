import sys
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def run_sql(sql):
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text(sql))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return False

def check_exists(table, column):
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            res = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column}'")).scalar()
            return res is not None
        except:
            return False

def apply_fix():
    # 1. New Columns
    for col in ["gerente_insumos", "gerente_pet"]:
        if not check_exists('tb_cidade_supervisor', col):
            print(f"Adding {col}...")
            run_sql(f"ALTER TABLE tb_cidade_supervisor ADD COLUMN {col} VARCHAR")
        else:
            print(f"{col} already exists.")

    # 2. Autoincrement (already partially done but let's ensure all)
    tables_to_fix = [
        ('tb_referencias', 'codigo'),
        ('tb_cidade_supervisor', 'codigo'),
        ('tb_canal_venda', 'Id'),
        ('tb_municipio_rota', 'id'),
        ('tb_supervisores', 'id')
    ]
    
    for table, pk in tables_to_fix:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            res = conn.execute(text(f"SELECT column_default FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{pk}'")).scalar()
            if not res or 'nextval' not in str(res):
                print(f"Fixing {table}.{pk}...")
                seq_name = f"{table}_{pk.lower()}_seq"
                run_sql(f"CREATE SEQUENCE IF NOT EXISTS {seq_name}")
                run_sql(f"ALTER TABLE {table} ALTER COLUMN {pk} SET DEFAULT nextval('{seq_name}')")
                run_sql(f"ALTER SEQUENCE {seq_name} OWNED BY {table}.{pk}")
                run_sql(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX({pk}) FROM {table}), 0) + 1, false)")

if __name__ == "__main__":
    apply_fix()
