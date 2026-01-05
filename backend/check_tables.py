from database import SessionLocal
from sqlalchemy import text

def inspect_tables():
    db = SessionLocal()
    try:
        # Check tables
        print("--- Tables ---")
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
        for t in tables:
            print(t[0])
            
        # Check specific table columns if it exists
        print("\n--- Columns in tb_pedido_historico (if exists) ---")
        try:
            cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tb_pedido_historico'")).fetchall()
            for c in cols:
                print(f"{c[0]}: {c[1]}")
        except Exception as e:
            print(f"Error inspecting specific table: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_tables()
