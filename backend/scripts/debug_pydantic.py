import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
from schemas.pedidos import PedidoResumo
from services.pedido_pdf_data import carregar_pedido_pdf

def debug_pydantic():
    try:
        with SessionLocal() as db:
            print("Carregando PID 10...")
            pdf = carregar_pedido_pdf(db, 10)
            print("Peso no PDF:", pdf.total_peso_liquido)
            
            # Simulando o dump Pydantic do resumo
            from services.pedidos import RESUMO_SQL
            head = dict(db.execute(RESUMO_SQL, {"id_pedido": 10}).mappings().first())
            from routers.pedidos import to_iso_or_none
            for k in ("validade_ate", "created_at", "atualizado_em", "data_prevista", "confirmado_em"):
                if k in head:
                    head[k] = to_iso_or_none(head[k])
                    
            head["itens"] = []
            head["peso_liquido_calculado"] = pdf.total_peso_liquido
            
            resumo = PedidoResumo(**head)
            print("Output Final em JSON:", resumo.model_dump()["peso_liquido_calculado"])
            
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    debug_pydantic()
