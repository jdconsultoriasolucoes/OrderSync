import os
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.schema import CreateTable
from dotenv import load_dotenv

load_dotenv(dotenv_path="e:\\OrderSync - Dev\\.env")
DEV_DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DEV_DB_URL)
metadata = MetaData()
inspector = inspect(engine)

target_tables = [
    "t_usuario", 
    "tb_pedido_historico", 
    "t_produto_supra", 
    "t_preco_produto_pdf_v2" # Assuming this is the full table name
]

print("-- DDL GENERATED FROM DEV DB --\n")

for t_name in target_tables:
    if inspector.has_table(t_name):
        try:
            table = Table(t_name, metadata, autoload_with=engine)
            print(CreateTable(table).compile(engine))
            print(";")
        except Exception as e:
            print(f"-- Error inspecting {t_name}: {e}")
    else:
        print(f"-- Table {t_name} not found in Dev DB")
