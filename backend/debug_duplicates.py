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

# Avoid connect_args if it causes issues, or try utf-8
engine = create_engine(DATABASE_URL, connect_args={'client_encoding': 'latin1'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_dupes():
    db = SessionLocal()
    try:
        print("Searching for duplicates (Same Code + Type)...")
        # Get codes that have duplicates
        sql_groups = text("""
            SELECT codigo_supra, tipo
            FROM public.t_cadastro_produto_v2
            WHERE status_produto = 'ATIVO'
            GROUP BY codigo_supra, tipo
            HAVING COUNT(*) > 1
            LIMIT 20;
        """)
        
        groups = db.execute(sql_groups).fetchall()
        print(f"Found {len(groups)} groups (showing top 20). Fetching details...")
        print("-" * 120)
        print(f"{'Code':<15} {'Type':<15} {'ID':<10} {'Provider'}")
        print("-" * 120)
        
        for g in groups:
            code = g[0]
            tipo = g[1]
            
            # Fetch details for this group
            sql_det = text("""
                SELECT id, fornecedor 
                FROM public.t_cadastro_produto_v2 
                WHERE codigo_supra = :c AND tipo = :t AND status_produto = 'ATIVO'
            """)
            
            details = db.execute(sql_det, {"c": code, "t": tipo}).fetchall()
            for d in details:
                pid = d[0]
                pname = d[1]
                
                # Safe print
                pname_safe = "NULL"
                if pname:
                    try:
                         pname_safe = str(pname).encode('ascii', errors='replace').decode('ascii')
                    except:
                         pname_safe = "ERR_ENCODE"
                         
                print(f"{code:<15} {tipo:<15} {pid:<10} {pname_safe}")
            print("-" * 120)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_dupes()
