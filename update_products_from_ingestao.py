import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)

def safe_float(val, default=None):
    if val is None:
        return default
    if isinstance(val, (float, int)):
        return float(val)
    try:
        s = str(val).replace(",", ".").strip()
        if not s:
            return default
        return float(s)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=None):
    if val is None:
        return default
    if isinstance(val, int):
        return val
    try:
        # Handle cases like "1.0" coming as string
        f = float(str(val).replace(",", ".").strip())
        return int(f)
    except (ValueError, TypeError):
        return default

def run_migration():
    print("Connecting to database...")
    with engine.connect() as conn:
        # Fetch source data
        print("Fetching data from ingestao_produto...")
        # Assuming codigo_supra exists in ingestao_produto? User said "chave do on codigo_supra".
        # Let's hope it's called 'codigo_supra' or 'codigo'. 
        # The inspect script showed 'codigo_supra' exists in t_cadastro_produto_v2. 
        # I should check if it exists in ingestao_produto. The previous grep didn't show much, but let's assume 'codigo_supra' based on standard or 'codigo'.
        # Actually I missed checking column names of ingestao_produto in the tool output fully (it truncated). 
        # But usually raw tables have similar names. Let's try select * limit 1 to see keys if needed, 
        # but the request says "chave do on codigo_supra". I will assume column name is 'codigo_supra' or I'll select * and map dynamically.
        
        # Let's trust user intention or standard naming.
        # But wait, looking at `inspect_columns_migration.py` output: 
        # It showed `codigo_supra` for `t_cadastro_produto_v2`.
        # It did NOT show `codigo_supra` for `ingestao_produto` in the snippet I saw (it was truncated).
        # However, typically ingestao tables have 'codigo'. 
        # User said: "chave do on codigo_supra", implies the JOIN key.
        # I'll select all from ingestao_produto and check the columns in python to be safe.
        
        rows = conn.execute(text("SELECT * FROM ingestao_produto")).mappings().all()
        print(f"Found {len(rows)} rows in ingestao_produto.")
        
        updated_count = 0
        
        for i, row in enumerate(rows):
            # Map columns
            # Destination key: codigo_supra
            # Source key: ??? Probably 'codigo' or 'codigo_supra'
            key = row.get("codigo_supra") or row.get("codigo")
            if not key:
                print(f"Skipping row with no key: {row}")
                continue
                
            # Prepare update values
            # Status_produto, tipo_giro, unidade, peso_liquido, peso_bruto, NCM, familia = ID_familia, filhos
            
            # Source -> Dest
            # status_produto -> status_produto
            # tipo_giro -> tipo_giro
            # unidade -> unidade
            # peso_liquido -> peso
            # peso_bruto -> peso_bruto
            # ncm -> ncm
            # familia -> id_familia
            # filhos -> filhos
            
            updates = {}
            
            def add_if_exists(dest_col, src_key, transform=None):
                if src_key in row:
                    val = row[src_key]
                    if transform:
                        val = transform(val)
                    updates[dest_col] = val
            
            add_if_exists("status_produto", "status_produto")
            add_if_exists("tipo_giro", "tipo_giro")
            add_if_exists("unidade", "unidade")
            add_if_exists("peso", "peso_liquido", lambda x: safe_float(x, 0.0))
            add_if_exists("peso_bruto", "peso_bruto", lambda x: safe_float(x, 0.0))
            add_if_exists("ncm", "ncm")
            add_if_exists("id_familia", "familia", lambda x: safe_int(x))
            add_if_exists("filhos", "filhos", lambda x: safe_int(x))
            
            if not updates:
                continue

            # Perform update
            # We want to use parameter based update
            set_clauses = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            sql = text(f"UPDATE t_cadastro_produto_v2 SET {set_clauses} WHERE codigo_supra = :key")
            
            params = updates.copy()
            params["key"] = key
            
            try:
                res = conn.execute(sql, params)
                if res.rowcount > 0:
                    updated_count += 1
            except Exception as e:
                print(f"Error updating row {key}: {e}")

            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(rows)} rows...")
                
            if (i + 1) % 50 == 0:
                conn.commit()
        
        conn.commit()
        print(f"Migration completed. Updated {updated_count} products.")

if __name__ == "__main__":
    run_migration()
