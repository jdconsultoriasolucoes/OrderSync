import sqlalchemy
from sqlalchemy import create_engine, inspect

db_url = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require"

try:
    print("Tentando conectar ao banco de dados DEV...")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Conexão DEV bem-sucedida! Tabelas: {tables}")
except Exception as e:
    print(f"Erro ao conectar ao banco DEV: {e}")
