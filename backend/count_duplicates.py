import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Config database handling
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ordersync_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Try standard connection, usually COUNT returns int which has no encoding issues
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def count_dupes_to_delete():
    db = SessionLocal()
    try:
        print("Counting duplicates to be deleted...")
        # Logic: 
        # Partition by (codigo, tipo). 
        # Order by: Votorantim (Priority 1), then Newer ID (Priority 2).
        # Any row with row_number > 1 is a duplicate "loser" to be deleted.
        
        sql = text("""
        SELECT COUNT(*) FROM (
            SELECT 
                id, 
                row_number() OVER (
                    PARTITION BY codigo_supra, tipo 
                    ORDER BY 
                        CASE WHEN fornecedor ILIKE '%VOTORANTIM%' THEN 1 ELSE 2 END ASC, -- 1 comes before 2
                        id DESC -- Prefer newest
                ) as rn
            FROM public.t_cadastro_produto_v2
            WHERE status_produto = 'ATIVO'
        ) t
        WHERE t.rn > 1;
        """)
        
        count = db.execute(sql).scalar()
        print(f"DUPLICATES FOUND: {count}")
    
    except Exception as e:
        # If even this fails, likely connection issue or critical db charset mismatch
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    count_dupes_to_delete()
