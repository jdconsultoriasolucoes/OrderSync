import os
# Hardcoded for debugging purposes
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from sqlalchemy import text
from database import SessionLocal

def inspect_tables():
    db = SessionLocal()
    try:
        print("--- Columns of t_cadastro_produto_v2 ---")
        res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_cadastro_produto_v2'"))
        cols = [f"{row[0]} ({row[1]})" for row in res]
        print("\n".join(sorted(cols)))

        print("\n--- Definition of v_produto_v2_preco (View) ---")
        # Try to get view definition (Postgres specific)
        res = db.execute(text("SELECT pg_get_viewdef('v_produto_v2_preco', true)"))
        print(res.scalar())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_tables()
