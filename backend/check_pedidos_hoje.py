import os
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
print("Orders today:")
query = """
SELECT id_pedido, status, data_faturamento, usar_valor_com_frete 
FROM tb_pedidos 
WHERE data_faturamento >= '2026-10-08'
"""
rows = db.execute(text(query)).fetchall()
for r in rows:
    print(r)
