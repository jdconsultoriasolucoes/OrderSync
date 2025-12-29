import sys
import os

# Adjust path to find database module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Check if columns exist (simple try/except approach or just allow failure if exists)
            print("Adding valor_final_markup...")
            conn.execute(text("ALTER TABLE tb_tabela_preco ADD COLUMN valor_final_markup NUMERIC(14, 2) DEFAULT 0 NOT NULL"))
            print("Added valor_final_markup.")
        except Exception as e:
            print(f"Skipping valor_final_markup (maybe exists): {e}")

        try:
            print("Adding valor_s_frete_markup...")
            conn.execute(text("ALTER TABLE tb_tabela_preco ADD COLUMN valor_s_frete_markup NUMERIC(14, 2) DEFAULT 0 NOT NULL"))
            print("Added valor_s_frete_markup.")
        except Exception as e:
            print(f"Skipping valor_s_frete_markup (maybe exists): {e}")

        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
