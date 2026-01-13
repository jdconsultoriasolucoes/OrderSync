import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def verify_schema():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set in env, using fallback")
        db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

    engine = create_engine(db_url)
    db = engine.connect()

    try:
        print("--- Columns of t_familia_produtos ---")
        res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_familia_produtos'"))
        cols = [f"{row[0]} ({row[1]})" for row in res]
        print("\n".join(sorted(cols)))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_schema()
