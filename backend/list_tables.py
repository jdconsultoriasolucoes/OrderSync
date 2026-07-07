import os
from sqlalchemy import text
from database import SessionLocal

def run():
    db = SessionLocal()
    try:
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
        print("TABLES:")
        for t in tables:
            print(t[0])
            
        print("Checking for LUCAS P. CORDEIRO in t_cadastro_cliente_v2 without ILIKE...")
        lucas = db.execute(text("SELECT * FROM t_cadastro_cliente_v2 WHERE cadastro_cnpj LIKE '%32250981%' OR cadastro_nome_cliente LIKE '%LUCAS%'")).fetchall()
        print(f"Found {len(lucas)} rows with 'LUCAS' or '32250981' in t_cadastro_cliente_v2")

    finally:
        db.close()

if __name__ == '__main__':
    run()
