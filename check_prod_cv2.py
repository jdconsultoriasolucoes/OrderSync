import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)
inspector = inspect(engine)

table_name = "t_cadastro_cliente_v2"

if inspector.has_table(table_name):
    print(f"Table '{table_name}' EXISTS in Prod.")
    columns = inspector.get_columns(table_name)
    print(f"Columns: {len(columns)}")
    for col in columns:
        print(f" - {col['name']} ({col['type']})")
else:
    print(f"Table '{table_name}' DOES NOT EXIST in Prod.")
