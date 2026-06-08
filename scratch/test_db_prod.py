import sqlalchemy
from sqlalchemy import create_engine, inspect

# URL fornecida pelo usuario
db_url_user = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
db_url_ssl = db_url_user + "?sslmode=require"

for url, label in [(db_url_user, "Sem SSL Explicit"), (db_url_ssl, "Com SSL Explicit")]:
    try:
        print(f"Tentando conectar ao banco PROD ({label})...")
        engine = create_engine(url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Conexão PROD bem-sucedida! Tabelas: {tables}")
        break
    except Exception as e:
        print(f"Erro ao conectar ({label}): {e}")
