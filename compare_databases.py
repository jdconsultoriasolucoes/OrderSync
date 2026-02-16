import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Carregar env do Dev
load_dotenv(dotenv_path="e:\\OrderSync - Dev\\.env")

DEV_DB_URL = os.getenv("DATABASE_URL")
PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

if not DEV_DB_URL:
    print("ERRO: DATABASE_URL não encontrada no .env de Dev")
    sys.exit(1)

def get_schema_info(db_url):
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema = {}
    try:
        tables = inspector.get_table_names()
        for table in tables:
            columns = inspector.get_columns(table)
            col_info = {col['name']: str(col['type']) for col in columns}
            schema[table] = col_info
    except Exception as e:
        print(f"Erro ao conectar em {db_url}: {e}")
        return None
    return schema

print("Conectando ao banco DEV...")
dev_schema = get_schema_info(DEV_DB_URL)

print("Conectando ao banco PROD...")
prod_schema = get_schema_info(PROD_DB_URL)

if not dev_schema or not prod_schema:
    sys.exit(1)

print("\n--- RELATÓRIO DE DIFERENÇAS DE BANCO DE DADOS ---\n")

all_tables = set(dev_schema.keys()) | set(prod_schema.keys())

for table in sorted(all_tables):
    if table not in prod_schema:
        print(f"[NOVO] Tabela '{table}' existe apenas no DEV.")
    elif table not in dev_schema:
        print(f"[REMOVIDO] Tabela '{table}' existe apenas em PROD.")
    else:
        # Check columns
        dev_cols = dev_schema[table]
        prod_cols = prod_schema[table]
        
        all_cols = set(dev_cols.keys()) | set(prod_cols.keys())
        diffs = []
        
        for col in sorted(all_cols):
            if col not in prod_cols:
                diffs.append(f"  + Coluna '{col}' ({dev_cols[col]}) adicionada no DEV")
            elif col not in dev_cols:
                diffs.append(f"  - Coluna '{col}' removida no DEV")
            elif dev_cols[col] != prod_cols[col]:
                diffs.append(f"  * Coluna '{col}' mudou tipo: PROD({prod_cols[col]}) -> DEV({dev_cols[col]})")
        
        if diffs:
            print(f"[MODIFICADO] Tabela '{table}':")
            for d in diffs:
                print(d)

print("\nConcluído.")
