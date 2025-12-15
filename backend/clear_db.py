from sqlalchemy import text
from database import SessionLocal

def clear_tables():
    db = SessionLocal()
    try:
        print("Clearing t_preco_produto_pdf_v2...")
        db.execute(text("TRUNCATE TABLE t_preco_produto_pdf_v2 RESTART IDENTITY CASCADE;"))
        
        print("Clearing t_cadastro_produto_v2...")
        db.execute(text("TRUNCATE TABLE t_cadastro_produto_v2 RESTART IDENTITY CASCADE;"))
        
        db.commit()
        print("Tables cleared and IDs reset successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_tables()
