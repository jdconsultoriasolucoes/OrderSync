import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking column names for v_produto_v2_preco:")
    res = conn.execute(text("SELECT * FROM public.v_produto_v2_preco LIMIT 1")).mappings().first()
    print(res.keys())
