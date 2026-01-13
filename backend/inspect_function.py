from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def inspect_function():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Fetching definition of trg_produto_v2_snapshot...")
        result = conn.execute(text("""
            SELECT pg_get_functiondef('trg_produto_v2_snapshot'::regproc);
        """)).scalar()
        
        print("\nFunction Definition:")
        print(result)

if __name__ == "__main__":
    inspect_function()
