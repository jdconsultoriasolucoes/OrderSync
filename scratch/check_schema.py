import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Columns for tb_pedidos_itens:")
    cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_pedidos_itens'")).fetchall()
    for c in cols:
        print(c[0])

    print("\nColumns for tb_tabela_preco:")
    cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_tabela_preco'")).fetchall()
    for c in cols:
        print(c[0])
