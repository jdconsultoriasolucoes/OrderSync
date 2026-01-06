import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Force load Env
load_dotenv(r"e:\OrderSync\.env")

PROD_DB_URL = os.getenv("PROD_DB_URL") 
if not PROD_DB_URL:
    PROD_DB_URL = os.getenv("DATABASE_URL")
if not PROD_DB_URL:
    PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def migrate_taxes():
    print("Fetching V1 products with tax info...")
    
    # 1. Fetch relevant tax columns from V1
    # Note: We only care about products that exist in V2 now.
    stmt = text("""
        SELECT codigo_supra, iva_st, ipi, icms 
        FROM t_cadastro_produto 
        WHERE (iva_st > 0 OR ipi > 0 OR icms > 0)
    """)
    v1_rows = session.execute(stmt).fetchall()
    print(f"Found {len(v1_rows)} V1 products with non-zero tax data.")

    # 2. Map V2 codes to IDs
    print("Mapping V2 codes to IDs...")
    v2_map = {} # code -> id
    v2_rows = session.execute(text("SELECT id, codigo_supra FROM t_cadastro_produto_v2")).fetchall()
    for r in v2_rows:
        if r.codigo_supra:
            v2_map[str(r.codigo_supra).strip()] = r.id
            
    print(f"Mapped {len(v2_map)} V2 products.")

    # 3. Insert/Update t_imposto_v2
    # First, let's see what's already in t_imposto_v2 to avoid duplicates or decide to update
    existing_tax_ids = set()
    rows_imposto = session.execute(text("SELECT produto_id FROM t_imposto_v2")).fetchall()
    for r in rows_imposto:
        existing_tax_ids.add(r.produto_id)
        
    count_insert = 0
    count_update = 0
    
    for row in v1_rows:
        code = str(row.codigo_supra or '').strip()
        if code not in v2_map:
            continue
            
        pid = v2_map[code]
        
        # Values
        iva_st_val = float(row.iva_st or 0)
        ipi_val = float(row.ipi or 0)
        icms_val = float(row.icms or 0)
        
        if pid in existing_tax_ids:
            # Update existing
            sql_upd = text("""
                UPDATE t_imposto_v2 
                SET iva_st = :iva, ipi = :ipi, icms = :icms
                WHERE produto_id = :pid
            """)
            session.execute(sql_upd, {"iva": iva_st_val, "ipi": ipi_val, "icms": icms_val, "pid": pid})
            count_update += 1
        else:
            # Insert new
            sql_ins = text("""
                INSERT INTO t_imposto_v2 (produto_id, iva_st, ipi, icms)
                VALUES (:pid, :iva, :ipi, :icms)
            """)
            session.execute(sql_ins, {"pid": pid, "iva": iva_st_val, "ipi": ipi_val, "icms": icms_val})
            existing_tax_ids.add(pid)
            count_insert += 1
            
    try:
        session.commit()
        print(f"Migration finished. Inserted: {count_insert}, Updated: {count_update}")
    except Exception as e:
        session.rollback()
        print(f"Error committing changes: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_taxes()
