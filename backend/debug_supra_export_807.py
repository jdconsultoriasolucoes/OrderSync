import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.cliente_v2 import ClienteModelV2
from services.excel_supra_service import gerar_excel_cliente_supra

def test_export():
    db = SessionLocal()
    try:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == 807).first()
        if not cliente:
            print("Cliente 807 não encontrado!")
            return
            
        print(f"Testando exportação para cliente {cliente.cadastro_nome_cliente}...")
        gerar_excel_cliente_supra(cliente)
        print("Sucesso! Nenhum erro de Python.")
    except Exception as e:
        print("====== ERRO CAPTURADO ======")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_export()
