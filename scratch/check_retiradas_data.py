from sqlalchemy import create_engine, text

url = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(url)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, numero_retirada, nome_retirada FROM tb_retiradas ORDER BY id ASC")).mappings().all()
    print("Total in tb_retiradas:", len(rows))
    for r in rows:
        print(f"ID: {r['id']} | num: {r['numero_retirada']} | nome: {r['nome_retirada']}")
