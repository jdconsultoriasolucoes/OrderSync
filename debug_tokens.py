import sys
import os
# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import SessionLocal
from sqlalchemy import text

try:
    with SessionLocal() as db:
        res = db.execute(text("SELECT id_pedido, link_token, created_at FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 5")).mappings().all()
        print("--- Last 5 Orders ---")
        for r in res:
            print(f"ID: {r.id_pedido} | Token: {r.link_token} | Created: {r.created_at}")
except Exception as e:
    print(f"Error: {e}")
