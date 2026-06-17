import sys
import os
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_preview_batch():
    # Make a request to /fiscal/preview-batch
    payload = {
        "cliente_codigo": None,
        "forcar_iva_st": False,
        "ramo_juridico": None,
        "itens": [
            {
                "cliente_codigo": None,
                "forcar_iva_st": False,
                "produto_id": "1",  # Let's see if 1 exists or not
                "preco_unit": 200.0,
                "quantidade": 1,
                "desconto_linha": 0.0,
                "frete_linha": 0.0
            }
        ]
    }
    
    resp = client.post("/fiscal/preview-batch", json=payload)
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.json())

if __name__ == "__main__":
    test_preview_batch()
