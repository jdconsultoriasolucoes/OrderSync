import sys
import os
from sqlalchemy import text

# Add backend root to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal

def migrate():
    print("Starting migration: t_cadastro_cliente.ramo_juridico -> t_cadastro_cliente_v2.cadastro_tipo_cliente")
    
    db = SessionLocal()
    try:
        # Check if tables exist and have some data (optional, but good for debug)
        res_v1 = db.execute(text("SELECT COUNT(*) FROM public.t_cadastro_cliente")).scalar()
        res_v2 = db.execute(text("SELECT COUNT(*) FROM public.t_cadastro_cliente_v2")).scalar()
        print(f"DEBUG: Found {res_v1} rows in source (v1) and {res_v2} rows in target (v2).")

        # Perform the Update
        # Using Postgres UPDATE ... FROM syntax for join behavior
        sql = text("""
            UPDATE public.t_cadastro_cliente_v2 v2
            SET cadastro_tipo_cliente = v1.ramo_juridico
            FROM public.t_cadastro_cliente v1
            WHERE v2.cadastro_codigo_da_empresa = CAST(v1.codigo AS TEXT)
              AND v1.ramo_juridico IS NOT NULL
        """)
        
        result = db.execute(sql)
        row_count = result.rowcount
        db.commit()
        
        print(f"SUCCESS: Migration completed. {row_count} rows were updated.")
        
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
