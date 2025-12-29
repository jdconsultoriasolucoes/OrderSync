
from sqlalchemy import create_engine, text
from database import DATABASE_URL
import time

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    res = conn.execute(text("SELECT COUNT(*) FROM t_cadastro_cliente_v2")).scalar()
    print(f"V2 Count: {res}")
