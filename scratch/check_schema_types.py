import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    cols = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tb_pedidos'")).fetchall()
    for c in cols:
        print(f"Column: {c[0]}, Type: {c[1]}")
