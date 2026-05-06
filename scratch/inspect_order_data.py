import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Pegar o ID do pedido mais recente para testar
with engine.connect() as conn:
    order = conn.execute(text("SELECT id_pedido, status, frete_kg, frete_total, peso_total_kg FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 1")).mappings().first()
    if order:
        id_ped = order['id_pedido']
        print(f"Testing ID: {id_ped}")
        print(f"Order Head: {dict(order)}")
        
        items = conn.execute(text("SELECT * FROM tb_pedidos_itens WHERE id_pedido = :id"), {"id": id_ped}).mappings().all()
        print(f"Items Count: {len(items)}")
        for i in items[:3]:
            print(f"  Item: {dict(i)}")
            
        # Test RESUMO_SQL join
        # Just a simple count of items linked to this order
        linked = conn.execute(text("SELECT COUNT(*) FROM tb_pedidos_itens c JOIN tb_pedidos a ON a.id_pedido = c.id_pedido WHERE a.id_pedido = :id"), {"id": id_ped}).scalar()
        print(f"Linked Items (via JOIN): {linked}")
    else:
        print("No orders found.")
