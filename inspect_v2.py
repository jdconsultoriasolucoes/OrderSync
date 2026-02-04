import sys
import os
sys.path.append('backend')
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from sqlalchemy import text

def inspect_client_v2(code):
    with SessionLocal() as db:
        print(f"Testing columns for code '{code}'...")
        
        # Test cadastro_codigo_da_empresa
        try:
            sql1 = text("SELECT * FROM t_cadastro_cliente_v2 WHERE cadastro_codigo_da_empresa::text = :code")
            res1 = db.execute(sql1, {"code": code}).mappings().first()
            if res1:
                 print("Match found! Relevant Fields:")
                 for k, v in res1.items():
                     if 'nome' in k or 'razao' in k or (v is not None and str(v).strip() != ''):
                         print(f"  {k}: {v}")
            else:
                 print("No match for cadastro_codigo_da_empresa")
        except Exception as e:
            print(f"Error checking cadastro_codigo: {e}")

if __name__ == "__main__":
    inspect_client_v2('210057')
