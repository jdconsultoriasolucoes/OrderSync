import os
import sys

# Add the project root to sys.path so we can import 'database'
project_root = os.path.dirname(os.path.abspath(__file__))
# If script is in backend/scripts/migration.py, root is ../..
# Assuming we run from backend root.
sys.path.append(os.getcwd())

try:
    from database import SessionLocal, engine
    from sqlalchemy import text, inspect
except ImportError:
    # Fallback if running from root without proper pythonpath
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from database import SessionLocal, engine
    from sqlalchemy import text, inspect

def add_column_if_not_exists():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('t_cadastro_produto_v2')]
    
    if 'marca' in columns:
        print("Column 'marca' already exists.")
        return

    print("Adding column 'marca'...")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE t_cadastro_produto_v2 ADD COLUMN marca TEXT;"))
        conn.commit()
    print("Column 'marca' added successfully.")

if __name__ == "__main__":
    add_column_if_not_exists()
