from database import SessionLocal
from sqlalchemy import text

def get_one_order():
    db = SessionLocal()
    try:
        row = db.execute(text("SELECT id_pedido, status, atualizado_por, atualizado_em FROM tb_pedidos ORDER BY created_at DESC LIMIT 1")).mappings().first()
        if row:
            print(f"ID: {row['id_pedido']}, Status: {row['status']}, UpdatedBy: {row['atualizado_por']}, UpdatedAt: {row['atualizado_em']}")
            return row['id_pedido']
        else:
            print("No orders found.")
            return None
    finally:
        db.close()

if __name__ == "__main__":
    get_one_order()
