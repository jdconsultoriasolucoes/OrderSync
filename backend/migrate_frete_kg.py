import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        print("Adicionando coluna frete_kg à tabela tb_pedidos...")
        try:
            conn.execute(text("ALTER TABLE tb_pedidos ADD COLUMN frete_kg FLOAT DEFAULT 0;"))
            conn.commit()
            print("Coluna adicionada com sucesso!")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("A coluna já existe.")
            else:
                print(f"Erro: {e}")

if __name__ == "__main__":
    migrate()
