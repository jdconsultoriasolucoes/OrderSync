import sys
import os
sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))
from database import SessionLocal
from sqlalchemy import text

def check_dispet():
    db = SessionLocal()
    try:
        print("--- BUSCANDO 'DISPET' ---")
        # Search by name or CNPJ snippet '7769327000171' from screenshot
        rows = db.execute(text("SELECT codigo, nome_empresarial, ramo_juridico FROM t_cadastro_cliente WHERE nome_empresarial ILIKE '%DISPET%' OR cnpj_cpf_faturamento ILIKE '%7769327000171%'")).mappings().all()
        for r in rows:
            print(dict(r))
        if not rows:
            print("Nenhum cliente encontrado com 'DISPET'.")
    finally:
        db.close()

if __name__ == "__main__":
    check_dispet()
