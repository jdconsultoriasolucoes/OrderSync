import os
from sqlalchemy import create_engine, inspect
from database import engine

def list_tables():
    inspector = inspect(engine)
    print("Tables:")
    for table_name in inspector.get_table_names():
        print(f" - {table_name}")

if __name__ == "__main__":
    list_tables()
