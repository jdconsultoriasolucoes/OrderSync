import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking tb_pedidos_itens content (top 5):")
    res = conn.execute(text("SELECT id_pedido, codigo, preco_unit, preco_unit_frt, valor_frete_unitario, manual_freight FROM tb_pedidos_itens ORDER BY id_item DESC LIMIT 5")).fetchall()
    for row in res:
        print(row)
