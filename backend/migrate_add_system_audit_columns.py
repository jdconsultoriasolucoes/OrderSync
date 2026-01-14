import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use correct fallback if needed, but here we assume env var or hardcoded one works
    DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def migrate():
    engine = create_engine(DATABASE_URL)
    tables = ['t_condicoes_pagamento', 't_desconto', 't_familia_produtos']
    
    with engine.connect() as conn:
        with conn.begin():
            for t in tables:
                print(f"Migrating table {t}...")
                
                # Check and add 'ativo'
                exists = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' AND column_name='ativo'")).scalar()
                if not exists:
                    print(f"Adding 'ativo' to {t}")
                    conn.execute(text(f"ALTER TABLE {t} ADD COLUMN ativo BOOLEAN DEFAULT TRUE"))
                
                # Check and add 'created_at'
                exists = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' AND column_name='created_at'")).scalar()
                if not exists:
                    print(f"Adding 'created_at' to {t}")
                    conn.execute(text(f"ALTER TABLE {t} ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))

                # Check and add 'updated_at'
                exists = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' AND column_name='updated_at'")).scalar()
                if not exists:
                    print(f"Adding 'updated_at' to {t}")
                    conn.execute(text(f"ALTER TABLE {t} ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"))

                # Check and add 'updated_by'
                exists = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' AND column_name='updated_by'")).scalar()
                if not exists:
                    print(f"Adding 'updated_by' to {t}")
                    conn.execute(text(f"ALTER TABLE {t} ADD COLUMN updated_by TEXT"))

    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
