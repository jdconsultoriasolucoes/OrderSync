import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Adicionando colunas de markup em tb_pedidos_itens...")
    try:
        conn.execute(text("""
            ALTER TABLE tb_pedidos_itens 
            ADD COLUMN markup NUMERIC(18,4) DEFAULT 0,
            ADD COLUMN valor_final_markup NUMERIC(14,2) DEFAULT 0,
            ADD COLUMN valor_s_frete_markup NUMERIC(14,2) DEFAULT 0;
        """))
        conn.commit()
        print("Colunas adicionadas com sucesso.")
    except Exception as e:
        print(f"Erro ao adicionar colunas: {e}")
