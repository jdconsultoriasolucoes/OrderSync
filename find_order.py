import sys
import os
sys.path.append('backend')
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from sqlalchemy import text

def find_order():
    with SessionLocal() as db:
        sql = text("SELECT id_pedido, codigo_cliente FROM tb_pedidos WHERE codigo_cliente ~ '^[0-9]+$' LIMIT 1")
        res = db.execute(sql).mappings().first()
        if res:
           print(f"Found Order: ID={res['id_pedido']}, ClientCode={res['codigo_cliente']}")
        else:
           print("No numeric code order found.")

if __name__ == "__main__":
    find_order()
