# backend/db/__init__.py
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ex.: postgres://user:pass@host:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine + pool (pre_ping evita conexões mortas no Render)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory (sincrono)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

# Dependency do FastAPI: abre/fecha sessão por request
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
