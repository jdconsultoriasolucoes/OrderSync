from database import SessionLocal
from sqlalchemy import text

def inspect_pedidos_columns():
    db = SessionLocal()
    try:
        print("--- Columns in tb_pedidos ---")
        cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tb_pedidos'")).fetchall()
        for c in cols:
            print(f"{c[0]}: {c[1]}")
    except Exception as e:
        print(f"Error inspecting tb_pedidos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_pedidos_columns()
