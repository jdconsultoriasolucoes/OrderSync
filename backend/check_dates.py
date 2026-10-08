import os
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
print("Distinct Statuses:")
statuses = db.execute(text("SELECT DISTINCT status FROM tb_pedidos")).fetchall()
for s in statuses:
    print(s[0])
