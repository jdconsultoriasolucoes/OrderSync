import sys
sys.path.append('e:/OrderSync/backend')
from database import SessionLocal
from services.cliente import _flat_to_nested
from schemas.cliente import ClienteCompleto
from models.cliente_v2 import ClienteModelV2
import traceback

def test_pydantic():
    db = SessionLocal()
    try:
        clientes = db.query(ClienteModelV2).all()
        print(f"Total clients fetched: {len(clientes)}")
        for i, c in enumerate(clientes):
            nested = _flat_to_nested(c)
            try:
                ClienteCompleto(**nested)
            except Exception as e:
                print(f"Validation failed for client ID {c.id}:")
                traceback.print_exc()
                break
    finally:
        db.close()

if __name__ == "__main__":
    test_pydantic()
