import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, nome, email, funcao, ativo FROM t_usuario"))
        users = result.fetchall()
        
        if not users:
            print("No users found in Production (Table is empty).")
        else:
            for u in users:
                print(f"User: {u.email} | Role: {u.funcao} | Active: {u.ativo}")
except Exception as e:
    print(f"Error querying users: {e}")
