import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]  # Render já fornece essa variável no ambiente

# opcional: pool_pre_ping=True evita “server closed the connection unexpectedly”
# Aumentado o pool para aguentar rajadas em ambiente SaaS
engine = create_engine(
    DATABASE_URL, 
    pool_size=20, 
    max_overflow=50, 
    pool_pre_ping=True, 
    pool_timeout=30
)

@event.listens_for(Engine, "connect")
def _set_timezone(dbapi_connection, connection_record):
    cur = dbapi_connection.cursor()
    try:
        cur.execute("SET TIME ZONE 'America/Sao_Paulo'")
    finally:
        cur.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()