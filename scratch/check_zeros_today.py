import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking for orders with zero total today:")
    res = conn.execute(text("SELECT id_pedido FROM tb_pedidos WHERE total_pedido = 0 AND created_at >= CURRENT_DATE")).fetchall()
    print(res)
