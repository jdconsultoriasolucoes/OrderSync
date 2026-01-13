import os
# Hardcoded for debugging purposes
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from sqlalchemy import text
from database import SessionLocal

def inspect_familia_table():
    db = SessionLocal()
    try:
        print("Checking columns of t_familia_produtos...")
        res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_familia_produtos'"))
        for row in res:
            print(f"{row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_familia_table()
