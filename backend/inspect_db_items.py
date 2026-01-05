from sqlalchemy import create_engine, text
import os
import sys
sys.path.append(os.getcwd())
from database import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tb_pedidos_itens';"))
    print("COLUNAS DE tb_pedidos_itens:")
    for row in result:
        print(f"{row[0]} ({row[1]})")
except Exception as e:
    print(f"Erro: {e}")
finally:
    db.close()
