from database import SessionLocal
from sqlalchemy import text

def add_column():
    db = SessionLocal()
    try:
        sql = "ALTER TABLE tb_pedidos ADD COLUMN IF NOT EXISTS atualizado_por VARCHAR(150);"
        print("Adding column 'atualizado_por' to tb_pedidos...")
        db.execute(text(sql))
        db.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_column()
