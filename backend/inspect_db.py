from sqlalchemy import create_engine, text
import os

# Assuming connection string or using default from codebase if I could load it.
# I'll try to load it from database.py or just use the one I saw earlier? 
# The codebase uses `database.py`. Let's assume I can import it.
# Actually I'd better just check database.py content to see the URL or try to use env var.
# Let's try to load standard session.

import sys
sys.path.append(os.getcwd())
from database import SessionLocal

db = SessionLocal()
try:
    # Inspect columns of tb_pedidos_itens
    result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tb_pedidos_itens';"))
    print("COLUNAS DE tb_pedidos_itens:")
    for row in result:
        print(f"{row[0]} ({row[1]})")

    # Also check tb_pedidos just in case
    result2 = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tb_pedidos';"))
    print("\nCOLUNAS DE tb_pedidos:")
    for row in result2:
        print(f"{row[0]} ({row[1]})")

except Exception as e:
    print(f"Erro: {e}")
finally:
    db.close()
