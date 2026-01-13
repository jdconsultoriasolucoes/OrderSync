from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

# Use the correct URL directly as verified in previous steps
DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def inspect_triggers():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Checking triggers for t_cadastro_produto_v2...")
        result = conn.execute(text("""
            SELECT trigger_name, event_manipulation, action_statement
            FROM information_schema.triggers
            WHERE event_object_table = 't_cadastro_produto_v2'
        """)).fetchall()
        
        if result:
            for row in result:
                print(f"Trigger: {row[0]}, Event: {row[1]}, Action: {row[2]}")
        else:
            print("No triggers found for t_cadastro_produto_v2.")

if __name__ == "__main__":
    inspect_triggers()
