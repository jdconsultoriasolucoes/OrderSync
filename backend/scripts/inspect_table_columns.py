
import pandas as pd
from sqlalchemy import create_engine
import sys

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

try:
    engine = create_engine(DB_URL)
    conn = engine.connect()
    print("Conectado.")
    
    # Check t_cadastro_cliente_v2
    print("Columns in t_cadastro_cliente_v2:")
    df = pd.read_sql("SELECT * FROM t_cadastro_cliente_v2 LIMIT 0", conn)
    with open("cols.txt", "w") as f:
        for col in df.columns:
            f.write(f"{col}\n")
    print("Columns written to cols.txt")
        
except Exception as e:
    print(f"Error: {e}")
