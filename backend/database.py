import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ["DATABASE_URL"]  # Render já fornece essa variável no ambiente

# opcional: pool_pre_ping=True evita “server closed the connection unexpectedly”
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@event.listens_for(Engine, "connect")
def _set_timezone(dbapi_connection, connection_record):
    cur = dbapi_connection.cursor()
    try:
        cur.execute("SET TIME ZONE 'America/Sao_Paulo'")
    finally:
        cur.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()