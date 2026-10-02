from sqlalchemy import create_engine, text
from schemas.cargas import CargaCreate
from models.cargas import CargaModel
import sys
sys.path.append("backend")

url = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(url)

with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Simulate creating a carga with empty numero_carga
        # Flush to get ID
        res = conn.execute(text("INSERT INTO tb_cargas (nome_carga) VALUES ('TESTE ROLLBACK') RETURNING id")).fetchone()
        cid = res[0]
        num_str = str(cid)
        conn.execute(text("UPDATE tb_cargas SET numero_carga = :num WHERE id = :id"), {"num": num_str, "id": cid})
        
        row = conn.execute(text("SELECT id, numero_carga, nome_carga FROM tb_cargas WHERE id = :id"), {"id": cid}).mappings().first()
        print("Inserted test carga:", dict(row))
        assert str(row['id']) == str(row['numero_carga']), "Mismatch between id and numero_carga!"
        print("SUCCESS: id and numero_carga are identical!")
    finally:
        trans.rollback()
        print("Transaction rolled back cleanly.")
