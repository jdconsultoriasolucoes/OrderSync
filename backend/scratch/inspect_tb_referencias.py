import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from sqlalchemy import text, inspect

def inspect_table():
    db = SessionLocal()
    try:
        # Check column details and default values (to see if it's serial)
        res = db.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'tb_referencias';
        """))
        cols = res.fetchall()
        print("Columns in tb_referencias:")
        for c in cols:
            print(f"- {c[0]} ({c[1]}) | Default: {c[2]}")
            
        # Also check if it's considered a primary key by SQLAlchemy
        inspector = inspect(engine)
        pks = inspector.get_pk_constraint("tb_referencias")
        print(f"\nPrimary Key Constraint: {pks}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_table()
