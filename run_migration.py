import os
from sqlalchemy import create_engine, text

# Conecta no DB
DATABASE_URL = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DATABASE_URL)

# Lê o SQL
sql_file_path = r"e:\OrderSync\historico_cliente_alteracoes.sql"
with open(sql_file_path, "r", encoding="utf-8") as f:
    sql_commands = f.read()

# Roda
with engine.connect() as conn:
    conn.execute(text(sql_commands))
    conn.commit()

print("Migração concluída com sucesso no banco de dados!")
