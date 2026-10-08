import os
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
from database import SessionLocal
from sqlalchemy import text
import unicodedata

def normalize_status(s):
    if not s:
        return "PEDIDO"
    s = s.strip().upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    
    if "FATURADO" in s and "SUPRA" in s: return "FATURADO_SUPRA"
    if "FATURADO" in s and "DISPET" in s: return "FATURADO_DISPET"
    if "CARGA" in s: return "CARGA_EM_FORMACAO"
    if "ORCAMENTO" in s: return "ORCAMENTO"
    if "CANCELADO" in s: return "CANCELADO"
    if "PEDIDO" in s: return "PEDIDO"
    if "ENTREGUE" in s: return "ENTREGUE"
    if "CONCLUIDO" in s: return "CONCLUIDO"
    
    return s.replace(" ", "_")

db = SessionLocal()
try:
    pedidos = db.execute(text("SELECT id_pedido, status FROM tb_pedidos")).fetchall()
    updated = 0
    for row in pedidos:
        old = row[1]
        new_status = normalize_status(old)
        if old != new_status:
            db.execute(text("UPDATE tb_pedidos SET status = :new_status WHERE id_pedido = :id"), {"new_status": new_status, "id": row[0]})
            updated += 1
    db.commit()
    print(f"Migration complete! {updated} records updated.")
finally:
    db.close()
