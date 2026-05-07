import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking items for order 9707:")
    res = conn.execute(text("SELECT id_pedido, codigo, preco_unit, preco_unit_frt, valor_frete_unitario, manual_freight, markup FROM tb_pedidos_itens WHERE id_pedido = 9707")).fetchall()
    for row in res:
        print(row)
