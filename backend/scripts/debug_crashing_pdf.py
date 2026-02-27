import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
from services.pedidos import LISTAGEM_SQL
from services.pedido_pdf_data import carregar_pedido_pdf
from datetime import datetime, timedelta

def debug_pdf():
    try:
        with SessionLocal() as db:
            rows = db.execute(LISTAGEM_SQL, {
                "from": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"), 
                "to": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), 
                "status_list": None, 
                "tabela_nome": None, 
                "cliente_busca": None, 
                "fornecedor_busca": None,
                "limit": 1,
                "offset": 0
            }).mappings().all()
            
            if not rows:
                print("No orders.")
                return
            
            pid = rows[0]["numero_pedido"]
            print(f"Testing PID: {pid}")
            pdf = carregar_pedido_pdf(db, pid)
            print("SUCCESS! Peso:", pdf.total_peso_liquido)
    except Exception as e:
        print("--- CRASHED ---")
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdf()
