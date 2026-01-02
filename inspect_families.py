
import os
from sqlalchemy import create_engine, text

# Using the URL provided by the user
DB_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def inspect_db():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("--- Table Columns (t_cadastro_produto_v2) ---")
            # Query columns
            res = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 't_cadastro_produto_v2'
            """))
            columns = [f"{row[0]} ({row[1]})" for row in res]
            print("\n".join(columns))

            print("\n--- Existing Families ---")
            # Check existing families and IDs
            res = conn.execute(text("""
                SELECT DISTINCT familia, id_familia 
                FROM t_cadastro_produto_v2 
                ORDER BY id_familia
            """))
            for row in res:
                print(f"ID: {row[1]}, Name: {row[0]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
