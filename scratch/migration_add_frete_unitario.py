import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Adicionando coluna valor_frete_unitario em tb_pedidos_itens...")
    try:
        conn.execute(text("ALTER TABLE tb_pedidos_itens ADD COLUMN valor_frete_unitario NUMERIC(14,2) DEFAULT 0;"))
        conn.commit()
        print("Coluna adicionada com sucesso.")
    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")
