import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def add_modelo_column():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found.")
        return

    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Checking if 'modelo' column exists in 'tb_transporte'...")
        # PostgreSql check
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tb_transporte' AND column_name='modelo'"))
        if not res.fetchone():
            print("Adding 'modelo' column to 'tb_transporte'...")
            conn.execute(text("ALTER TABLE tb_transporte ADD COLUMN modelo VARCHAR NULL"))
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'modelo' already exists.")

if __name__ == "__main__":
    add_modelo_column()
