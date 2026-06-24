import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM public.pedido_status")).mappings().all()
        for r in res:
            print(dict(r))
except Exception as e:
    print(f"Erro: {e}")
