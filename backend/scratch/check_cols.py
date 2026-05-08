import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # try to read from a local .env or config if you know where it is
    # but for now, let's assume it's in the environment as is common in this setup
    print("DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 't_cadastro_cliente_v2'"))
    cols = [r[0] for r in res]
    print("\n".join(cols))
