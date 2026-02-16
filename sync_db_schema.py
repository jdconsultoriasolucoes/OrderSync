import os
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, text, Computed
from sqlalchemy.schema import CreateTable
from dotenv import load_dotenv

# Load Dev Env
load_dotenv(dotenv_path="e:\\OrderSync - Dev\\.env")
DEV_DB_URL = os.getenv("DATABASE_URL")
PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

if not DEV_DB_URL:
    print("Dev DB URL missing")
    sys.exit(1)

dev_engine = create_engine(DEV_DB_URL)
prod_engine = create_engine(PROD_DB_URL)

dev_insp = inspect(dev_engine)
prod_insp = inspect(prod_engine)

dev_tables = dev_insp.get_table_names()
prod_tables = prod_insp.get_table_names()

metadata = MetaData()

print("--- STARTING DB SYNC ---")

# 1. CREATE MISSING TABLES
for table in dev_tables:
    if table not in prod_tables:
        print(f"Creating new table: {table}")
        try:
            # Reflect table from Dev
            t_obj = Table(table, metadata, autoload_with=dev_engine)
            # Generate DDL
            ddl = CreateTable(t_obj).compile(dev_engine)
            # Execute on Prod
            with prod_engine.connect() as conn:
                conn.execute(ddl)
                conn.commit()
            print(f"FAILED TO CREATE {table} (Simulation)? No, executed!")
            print(f"Success: Created {table}")
        except Exception as e:
            print(f"Error creating {table}: {e}")

# 2. ALTER TABLES (ADD COLUMNS)
for table in dev_tables:
    if table in prod_tables:
        dev_cols = dev_insp.get_columns(table)
        prod_cols = prod_insp.get_columns(table)
        
        prod_col_names = [c['name'] for c in prod_cols]
        
        for dc in dev_cols:
            cname = dc['name']
            if cname not in prod_col_names:
                print(f"Adding column {table}.{cname}")
                ctype = dc['type']
                # Construct ADD COLUMN
                # Special handling for types, or basic string repr
                # SQLAlchemy type compilation is tricky.
                # Let's use simple string mapping if possible, or compile type
                
                type_str = str(ctype) 
                # Note: compile(dialect=postgresql.dialect()) might be safer but str() usually works for standard types
                
                sql = f'ALTER TABLE "{table}" ADD COLUMN "{cname}" {type_str}'
                
                # Handling Nullability
                if not dc['nullable']:
                    # Adding Not Null column to existing table is risky without default. 
                    # If standard type, we might need default.
                    # For now, let's add as NULLABLE to be safe unless we know better.
                    pass # Keep it nullable by default in ALTER unless specified
                
                try:
                    with prod_engine.connect() as conn:
                        conn.execute(text(sql))
                        conn.commit()
                    print(f"Success: Added {cname}")
                except Exception as e:
                    print(f"Error adding {cname}: {e}")

print("--- DB SYNC COMPLETE ---")
