import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text
from update_view import update_view

def run_migration():
    with engine.connect() as conn:
        print("Checking if 'estoque_futuro' column exists in 't_cadastro_produto_v2'...")
        res = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='t_cadastro_produto_v2' AND column_name='estoque_futuro'"
        ))
        row = res.fetchone()
        if not row:
            print("Adding 'estoque_futuro' column to 't_cadastro_produto_v2'...")
            conn.execute(text("ALTER TABLE t_cadastro_produto_v2 ADD COLUMN estoque_futuro INTEGER NULL"))
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'estoque_futuro' already exists.")

    print("Updating database views...")
    update_view()
    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
