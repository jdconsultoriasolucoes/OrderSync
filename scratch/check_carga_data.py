from sqlalchemy import create_engine, text

url = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(url)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, numero_carga, nome_carga, is_retirada FROM tb_cargas ORDER BY id ASC")).mappings().all()
    for r in rows:
        print(f"ID: {r['id']} | num: {r['numero_carga']} | nome: {r['nome_carga']} | ret: {r['is_retirada']}")
