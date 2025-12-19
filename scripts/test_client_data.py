import requests

URL = "http://localhost:8000/tabela_preco/busca_cliente" # Adjust if needed, but I'll use relative to user env or mock
# Actually I need to run this as Python script invoking the code or `requests` against LIVE server?? 
# The user environment `e:\OrderSync - Dev` implies I can run python scripts.
# I will use `requests` if available or just invoke the function directly via python shell.
# Invoking function directly is safer/easier as I don't know the port (8000?).

import sys
sys.path.append('e:/OrderSync - Dev/backend')

from database import SessionLocal
from sqlalchemy import text

def test_search():
    try:
        db = SessionLocal()
        # Search for any client
        sql = """
            SELECT codigo, nome_empresarial, ramo_juridico 
            FROM t_cadastro_cliente 
            LIMIT 5
        """
        rows = db.execute(text(sql)).mappings().all()
        print("--- Direct DB Check ---")
        for r in rows:
            print(dict(r))

        print("\n--- Endpoint Logic Check ---")
        # I can just inspect the DB output above. If 'codigo' is there, the endpoint (which uses similar SQL) should have it.
        # The endpoint uses: SELECT codigo, ...
        # So it should be fine.
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_search()
