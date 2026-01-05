from database import SessionLocal
from sqlalchemy import text

def check_data():
    db = SessionLocal()
    try:
        # Check distinct status values
        print("--- Status Values ---")
        res = db.execute(text("SELECT DISTINCT status_produto FROM t_cadastro_produto_v2"))
        for row in res:
            print(f"Status: '{row[0]}'")

        # Check a sample product date
        print("\n--- Sample Product Dates (Active) ---")
        res = db.execute(text("SELECT id, validade_tabela FROM t_cadastro_produto_v2 WHERE status_produto = 'ATIVO' LIMIT 5"))
        for row in res:
            print(f"ID: {row[0]}, Validade: {row[1]}")
            
    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
