import sys
import os

# Add backend directory to path so we can import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from database import SessionLocal
    from sqlalchemy import text
    
    with SessionLocal() as db:
        print("--- LAST 5 ORDERS ---")
        rows = db.execute(text("""
            SELECT id_pedido, cliente, link_token, status, criado_em 
            FROM tb_pedidos 
            ORDER BY id_pedido DESC 
            LIMIT 5
        """)).mappings().all()
        
        for r in rows:
            print(f"ID: {r['id_pedido']} | Token: '{r['link_token']}' | Status: {r['status']} | Cliente: {r['cliente']}")
            
except Exception as e:
    print(f"Error: {e}")
