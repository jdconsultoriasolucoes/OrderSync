from sqlalchemy import create_engine, text
import os
import sys
sys.path.append(os.getcwd())
from database import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text("SELECT * FROM tb_pedidos_itens LIMIT 1;"))
    print("DADOS DE tb_pedidos_itens (1 linha):")
    row = result.mappings().first()
    if row:
        for k, v in row.items():
            print(f"{k}: {v}")
    else:
        print("Tabela vazia.")
except Exception as e:
    print(f"Erro: {e}")
finally:
    db.close()
