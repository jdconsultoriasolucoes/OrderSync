import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking for manual freight items:")
    res = conn.execute(text("SELECT id_pedido, codigo, manual_freight, valor_frete_unitario FROM tb_pedidos_itens WHERE manual_freight IS TRUE LIMIT 10")).fetchall()
    for row in res:
        print(row)
