import os
from sqlalchemy import create_engine, inspect

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)
inspector = inspect(engine)

print("-- V1 PRODUCT COLUMNS --")
columns = inspector.get_columns('t_cadastro_produto')
for c in columns:
    print(c['name'])
