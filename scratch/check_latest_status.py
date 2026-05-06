import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    order = conn.execute(text("SELECT id_pedido, status FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 1")).mappings().first()
    print(f"ID: {order['id_pedido']}, Status: '{order['status']}'")
