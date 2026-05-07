import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking totals for order 9707:")
    res = conn.execute(text("SELECT id_pedido, total_pedido, total_sem_frete, total_com_frete FROM tb_pedidos WHERE id_pedido = 9707")).first()
    print(res)
