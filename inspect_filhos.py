
import os
from sqlalchemy import create_engine, text

DB_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def inspect_db_filhos():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("--- checking t_cadastro_produto_v2 for 'filhos' ---")
            res = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 't_cadastro_produto_v2' AND column_name = 'filhos'
            """))
            rows = list(res)
            if rows:
                print(f"FOUND: {rows[0][0]} ({rows[0][1]})")
            else:
                print("NOT FOUND: 'filhos' column missing in t_cadastro_produto_v2")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db_filhos()
