from sqlalchemy import text
from database import SessionLocal

db = SessionLocal()
try:
    print("--- Checking Order 204 ---")
    sql = text("SELECT * FROM public.tb_pedidos WHERE id_pedido = 204")
    row = db.execute(sql).first()
    if row:
        print(f"Found Order 204: {row}")
    else:
        print("Order 204 NOT FOUND locally.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
