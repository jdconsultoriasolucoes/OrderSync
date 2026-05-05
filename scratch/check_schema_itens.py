import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

table = "tb_pedidos_itens"
cols = inspector.get_columns(table)
for c in cols:
    print(f"Col: {c['name']}, Type: {c['type']}")
