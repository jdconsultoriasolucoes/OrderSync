from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def inspect_tables():
    engine = create_engine(DATABASE_URL)
    tables = ['t_condicoes_pagamento', 't_desconto', 't_familia_produtos']
    
    with engine.connect() as conn:
        for t in tables:
            print(f"--- Table: {t} ---")
            cols = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{t}'
                ORDER BY ordinal_position
            """)).fetchall()
            for c in cols:
                print(f"  {c[0]} ({c[1]}) - Nullable: {c[2]}")
            print("")

if __name__ == "__main__":
    inspect_tables()
