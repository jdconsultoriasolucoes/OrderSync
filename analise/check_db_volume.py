
import os
import sys

# Setup paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Hardcoded for debugging purposes (copied from existing script to ensure connection)
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from sqlalchemy import text
from backend.database import SessionLocal

def check_volume():
    db = SessionLocal()
    try:
        print("--- Volume Analysis ---")
        
        # 1. Total Active Price Tables (Headers)
        res_tables = db.execute(text("SELECT COUNT(*) FROM tb_tabela_preco WHERE ativo IS TRUE")).scalar()
        print(f"Active Price Tables: {res_tables}")

        # 2. Total Items in Price Tables (Lines that would need updating)
        # Note: Since the table is localized per 'tabela', we just count rows
        res_items = db.execute(text("SELECT COUNT(*) FROM tb_tabela_preco WHERE ativo IS TRUE AND codigo_produto_supra IS NOT NULL")).scalar()
        print(f"Total Price Table Items (Rows to update): {res_items}")

        # 3. Total Source Products
        res_prods = db.execute(text("SELECT COUNT(*) FROM t_cadastro_produto_v2 WHERE status_produto = 'ATIVO'")).scalar()
        print(f"Total Source Products (Catalog): {res_prods}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_volume()
