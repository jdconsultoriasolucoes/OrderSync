import sqlalchemy as sa
from sqlalchemy import inspect
import json

def get_schema(url):
    engine = sa.create_engine(url)
    inspector = inspect(engine)
    schema = {}
    
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"]
            })
        schema[table_name] = columns
    
    return schema

dev_url = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"
prod_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

print("Fetching DEV schema...")
dev_schema = get_schema(dev_url)

print("Fetching PROD schema...")
prod_schema = get_schema(prod_url)

# Compare
missing_in_prod = {}

for table, cols in dev_schema.items():
    if table not in prod_schema:
        missing_in_prod[table] = {"status": "MISSING_TABLE", "columns": cols}
    else:
        prod_cols = {c["name"] for c in prod_schema[table]}
        missing_cols = [c for c in cols if c["name"] not in prod_cols]
        if missing_cols:
            missing_in_prod[table] = {"status": "MISSING_COLUMNS", "columns": missing_cols}

print("\n--- DIFFERENCES (Missing in PROD) ---")
with open("scratch/schema_diff.json", "w") as f:
    json.dump(missing_in_prod, f, indent=2)
print("Differences written to scratch/schema_diff.json")
