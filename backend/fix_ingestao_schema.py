import os
from sqlalchemy import create_engine, text

# URL from migrate_products_prod.py
PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def fix_schema():
    print("Connecting to database...")
    engine = create_engine(PROD_DB_URL)
    
    # Check current column type (optional, but good for log)
    check_sql = text("""
        SELECT character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'ingestao_produto' AND column_name = 'nome_produto'
    """)
    
    with engine.connect() as conn:
        result = conn.execute(check_sql).fetchone()
        if result:
            print(f"Current length: {result[0]}")
        else:
            print("Table or column not found! Proceeding anyway in case it's in public schema but query missed it.")

        print("Altering table schema...")
        alter_sql = text("ALTER TABLE public.ingestao_produto ALTER COLUMN nome_produto TYPE VARCHAR(255)")
        conn.execute(alter_sql)
        conn.commit()
        print("Schema altered successfully.")

        # Verify
        result = conn.execute(check_sql).fetchone()
        if result:
             print(f"New length: {result[0]}")

if __name__ == "__main__":
    fix_schema()
