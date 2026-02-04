import sys
import os
sys.path.append('backend')
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from services.pedido_pdf_data import carregar_pedido_pdf

def verify_razao_social(pedido_id):
    with SessionLocal() as db:
        try:
            pedido = carregar_pedido_pdf(db, pedido_id)
            print(f"--- Verificacao Pedido {pedido_id} ---")
            print(f"Razão Social (Data Object): '{pedido.razao_social}'")
            print(f"Nome Fantasia (Fallback): '{pedido.nome_fantasia}'")
            print(f"Nome Cliente (Backup): '{pedido.cliente}'")
            
            if pedido.razao_social:
                print("SUCESSO: Razão Social foi populada.")
            else:
                print("FALHA: Razão Social está vazia.")
            
        except Exception as e:
            print(f"Erro ao carregar pedido: {e}")

if __name__ == "__main__":
    verify_razao_social(233)
