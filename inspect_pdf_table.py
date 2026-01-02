
import os
from sqlalchemy import create_engine, text

DB_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def inspect_pdf_table():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("--- Table Columns (t_preco_produto_pdf_v2) ---")
            res = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 't_preco_produto_pdf_v2'
            """))
            columns = [f"{row[0]} ({row[1]})" for row in res]
            print("\n".join(columns))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_pdf_table()
