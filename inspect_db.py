import sys
import os
sys.path.append('backend')
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from sqlalchemy import text

def inspect_columns():
    with SessionLocal() as db:
        sql = text("SELECT * FROM t_cadastro_cliente LIMIT 1")
        result = db.execute(sql).mappings().first()
        if result:
            print(f"Columns: {sorted(result.keys())}")
        else:
            print("Table seems empty or could not be read.")

if __name__ == "__main__":
    inspect_columns()
