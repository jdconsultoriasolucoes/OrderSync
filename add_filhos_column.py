
import os
from sqlalchemy import create_engine, text

DB_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def migrate_db():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("Checking if 'filhos' column exists in 't_preco_produto_pdf_v2'...")
            res = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 't_preco_produto_pdf_v2' AND column_name = 'filhos'
            """))
            if res.rowcount == 0:
                print("Column 'filhos' NOT found. Adding it...")
                conn.execute(text("ALTER TABLE t_preco_produto_pdf_v2 ADD COLUMN filhos INTEGER"))
                conn.commit()
                print("Column 'filhos' added successfully.")
            else:
                print("Column 'filhos' ALREADY EXISTS.")

    except Exception as e:
        print(f"Error: {e}")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    migrate_db()
