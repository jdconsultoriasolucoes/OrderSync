import sys
import os
sys.path.append('backend')
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from sqlalchemy import text

def inspect_client():
    # Fetch order 304 to get code
    with SessionLocal() as db:
        res = db.execute(text("SELECT codigo_cliente FROM tb_pedidos WHERE id_pedido = 304")).mappings().first()
        if not res:
            print("Order 304 not found")
            return
        
        code = res['codigo_cliente']
        print(f"Order 304 Client Code: '{code}'")
        
        # Now fetch client
        sql = text("SELECT * FROM t_cadastro_cliente WHERE codigo::text = :code")
        client = db.execute(sql, {"code": code}).mappings().first()
        
        if client:
            print("Client found:")
            print(f"  nome_empresarial: '{client.get('nome_empresarial')}'")
            print(f"  nome_fantasia: '{client.get('nome_fantasia')}'")
            print(f"  codigo: '{client.get('codigo')}'")
        else:
            print("Client NOT found in t_cadastro_cliente")

if __name__ == "__main__":
    with SessionLocal() as db:
        code = '210057'
        sql = text("SELECT * FROM t_cadastro_cliente WHERE codigo::text = :code")
        res = db.execute(sql, {"code": code}).mappings().first()
        if res:
             print(f"Old Table Match: {res.get('nome_empresarial')}")
        else:
             print("Client 210057 NOT FOUND in t_cadastro_cliente")
