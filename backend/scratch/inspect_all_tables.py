import sys
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def inspect_all():
    engine = create_engine(DATABASE_URL)
    tables = [
        ('tb_canal_venda', 'Id'),
        ('tb_cidade_supervisor', 'codigo'),
        ('tb_municipio_rota', 'id'),
        ('tb_referencias', 'codigo'),
        ('tb_supervisores', 'id'),
        ('tb_plantel_animais', 'id')
    ]
    
    with engine.connect() as conn:
        print("Inspecting tables sequence status:")
        for table, pk in tables:
            try:
                res = conn.execute(text(f"""
                    SELECT column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{pk}'
                """)).scalar()
                print(f"- {table}.{pk}: Default = {res}")
            except Exception as e:
                print(f"- {table}: Error {e}")
        
        print("\nChecking columns for tb_cidade_supervisor:")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_cidade_supervisor'"))
        cols = [r[0] for r in res]
        print(f"Columns: {cols}")

if __name__ == "__main__":
    inspect_all()
