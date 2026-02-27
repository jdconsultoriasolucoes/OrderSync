import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
from services.pedido_pdf_data import carregar_pedido_pdf
from services.pedidos import RESUMO_SQL

def test():
    try:
        with SessionLocal() as db:
            print("Querying hardcoded ID 89 (used previously, or 10, or another random row)...")
            from services.pedidos import LISTAGEM_SQL
            from datetime import datetime, timedelta
            
            rows = db.execute(LISTAGEM_SQL, {
                "from": "2020-01-01", 
                "to": "2030-01-01", 
                "status_list": None, 
                "tabela_nome": None, 
                "cliente_busca": None, 
                "fornecedor_busca": None,
                "limit": 1,
                "offset": 0
            }).mappings().all()
            
            if not rows:
                print("No rows.")
                return
            
            pid = rows[0]["numero_pedido"]
            print("Testing PID:", pid)
            
            head = db.execute(RESUMO_SQL, {"id_pedido": pid}).mappings().first()
            if not head:
                print("Head empty")
                return
                
            head_dict = dict(head)
            pdf = carregar_pedido_pdf(db, pid)
            
            print("PDF Native Peso Liq:", pdf.total_peso_liquido)
            head_dict["peso_liquido_calculado"] = pdf.total_peso_liquido
            
            print("MAPPED VALUE:", head_dict["peso_liquido_calculado"])
            print("IS ZERO?", head_dict["peso_liquido_calculado"] == 0 or head_dict["peso_liquido_calculado"] == 0.0)
            
    except Exception as e:
        print("FAILED TO MAP")
        traceback.print_exc()

if __name__ == "__main__":
    test()
