import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import text
from backend.database import SessionLocal
from datetime import datetime

def check_date():
    with SessionLocal() as db:
        print("Checking max validade_tabela...")
        sql = text("""
            SELECT MAX(CAST(p.validade_tabela AS DATE)) AS max_validade
            FROM t_cadastro_produto_v2 p
            WHERE p.status_produto = 'ATIVO'
        """)
        v = db.execute(sql).scalar()
        print(f"Max Validade: {v}")
        print(f"Hoje: {datetime.now().date()}")
        if v and v < datetime.now().date():
            print("ALERT: Validity is in the past!")
        elif not v:
             print("ALERT: No validity found!")
        else:
             print("Validity is future/today. OK.")

if __name__ == "__main__":
    check_date()
