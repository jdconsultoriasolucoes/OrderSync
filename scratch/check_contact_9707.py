import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking contact for order 9707:")
    res = conn.execute(text("SELECT contato_nome, contato_email, contato_fone FROM tb_pedidos WHERE id_pedido = 9707")).first()
    print(res)
