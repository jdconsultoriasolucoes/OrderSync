import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking tb_pedidos columns:")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_pedidos'")).fetchall()
    for row in res:
        print(row)
