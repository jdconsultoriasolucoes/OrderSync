import os
from sqlalchemy import create_engine, text, inspect

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)
inspector = inspect(engine)

v1_tables = [t for t in inspector.get_table_names() if 'produto' in t.lower()]
print(f"Product Tables Found: {v1_tables}")

print("-- ROW COUNTS --")
with engine.connect() as conn:
    for t in v1_tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"{t}: {count} rows")
        except Exception as e:
            print(f"{t}: Error {e}")
