from database import SessionLocal
from services.pedidos import STATUS_UPDATE_SQL, STATUS_EVENT_INSERT_SQL
from sqlalchemy import text
import pprint

def test_status_update():
    db = SessionLocal()
    id_pedido = 46
    new_status = "EM SEPARAÇÃO"
    user_id = "test_user"

    try:
        print(f"Attempting to update Order {id_pedido} to {new_status}")
        
        # 1. Update Status
        upd = db.execute(STATUS_UPDATE_SQL, {
            "para_status": new_status, 
            "id_pedido": id_pedido,
            "user_id": user_id
        }).first()
        
        if upd:
            print(f"Update returned ID: {upd.id_pedido}")
        else:
            print("Update returned None")
            return

        # 2. Insert Event (mimicking router)
        try:
            print("Attempting to insert event...")
            with db.begin_nested():
                db.execute(STATUS_EVENT_INSERT_SQL, {
                    "pedido_id": id_pedido,
                    "de_status": "CONFIRMADO",
                    "para_status": new_status,
                    "user_id": user_id,
                    "motivo": "Test script",
                    "metadata": "{}"
                })
            print("Event insert returned success")
        except Exception as e:
            print(f"Event insert FAILED (caught): {e}")
            # Router does 'pass' here

        # 3. Commit
        print("Committing...")
        db.commit()
        print("Commit successful.")
        
        # 4. Verify
        row = db.execute(text("SELECT status, atualizado_por FROM tb_pedidos WHERE id_pedido = :id"), {"id": id_pedido}).mappings().first()
        print(f"VERIFICATION: Status={row['status']}, UpdatedBy={row['atualizado_por']}")

    except Exception as e:
        print(f"Top level error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_status_update()
