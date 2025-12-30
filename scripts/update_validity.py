import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import text
from backend.database import SessionLocal

def update_dates():
    with SessionLocal() as db:
        print("Updating active products validity to 2026-12-31...")
        sql = text("""
            UPDATE t_cadastro_produto_v2
            SET validade_tabela = '2026-12-31'
            WHERE status_produto = 'ATIVO'
        """)
        result = db.execute(sql)
        db.commit()
        print(f"Updated {result.rowcount} rows.")

if __name__ == "__main__":
    update_dates()
