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

# Adding client_encoding might help, but let's just be raw safe
engine = create_engine(DATABASE_URL, connect_args={'client_encoding': 'latin1'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_query():
    db = SessionLocal()
    try:
        # Check rows existence first
        print("Checking count...")
        count_sql = text("""
        select count(*)
        from public.t_cadastro_produto_v2 a
        join public.t_preco_produto_pdf_v2 b
        on a.codigo_supra = b.codigo
        where tipo = 'PET' and status_produto  = 'ATIVO' 
        and b.data_ingestao = '2026-01-07' 
        and b.validade_tabela = '2026-08-01' 
        and lista = 'PET';
        """)
        
        count = db.execute(count_sql).scalar()
        print(f"DEBUG: Found {count} mismatched rows.")
        
        if count > 0:
            # Fetch raw bytes as hex
            print("Fetching sample rows (HEX)...")
            hex_sql = text("""
            select a.codigo_supra, encode(a.fornecedor::bytea, 'hex') as forn_hex
            from public.t_cadastro_produto_v2 a
            join public.t_preco_produto_pdf_v2 b
            on a.codigo_supra = b.codigo
            where tipo = 'PET' and status_produto  = 'ATIVO' 
            and b.data_ingestao = '2026-01-07' 
            and b.validade_tabela = '2026-08-01' 
            and lista = 'PET'
            LIMIT 5;
            """)
            
            rows = db.execute(hex_sql).fetchall()
            print("First 5 Mismatched Rows (Code, ProviderHEX):")
            for r in rows:
                code = r[0]
                f_hex = r[1]
                print(f"Code: {code} | FornHex: {f_hex}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_query()
