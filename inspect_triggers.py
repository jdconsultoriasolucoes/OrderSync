
import os
from sqlalchemy import create_engine, text

DB_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def list_triggers():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("--- Triggers on t_cadastro_produto_v2 ---")
            res = conn.execute(text("""
                SELECT trigger_name, event_manipulation, action_statement
                FROM information_schema.triggers
                WHERE event_object_table = 't_cadastro_produto_v2'
            """))
            rows = list(res)
            if not rows:
                print("No triggers found.")
            else:
                for row in rows:
                    print(f"Trigger: {row[0]}, Event: {row[1]}")
                    print(f"Action: {row[2]}")
                    print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_triggers()
