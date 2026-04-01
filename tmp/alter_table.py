import sys
import os

# Ensure backend allows imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from database import SessionLocal
from sqlalchemy import text

def alter_table():
    db = SessionLocal()
    try:
        # Check if columns exist
        db.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN canal_id INTEGER;"))
        db.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN canal_tipo VARCHAR;"))
        db.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN canal_linha VARCHAR;"))
        db.commit()
        print("Columns added successfully.")
    except Exception as e:
        print("Error or columns probably already exist:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    alter_table()
