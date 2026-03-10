from database import engine
from sqlalchemy import text

def add_modelo_column():
    with engine.connect() as conn:
        print("Checking if 'modelo' column exists in 'tb_transporte'...")
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
