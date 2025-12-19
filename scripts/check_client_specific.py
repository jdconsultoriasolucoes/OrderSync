import sys
import os
sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))
from database import SessionLocal
from sqlalchemy import text

def check_angolana():
    db = SessionLocal()
    try:
        print("--- BUSCANDO 'ANGOLANA' ---")
        rows = db.execute(text("SELECT codigo, nome_empresarial, ramo_juridico FROM t_cadastro_cliente WHERE nome_empresarial ILIKE '%ANGOLANA%'")).mappings().all()
        for r in rows:
            print(dict(r))
        if not rows:
            print("Nenhum cliente encontrado com 'ANGOLANA'.")
    finally:
        db.close()

if __name__ == "__main__":
    check_angolana()
