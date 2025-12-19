import sys
import os

sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))

from database import SessionLocal
from sqlalchemy import text

def inspect_recent_prices():
    db = SessionLocal()
    try:
        # Check last 5 created tables (assuming id_tabela implies creation order/time)
        sql = """
            SELECT 
                id_tabela, 
                nome_tabela, 
                cliente, 
                codigo_cliente, 
                calcula_st 
            FROM tb_tabela_preco 
            ORDER BY id_tabela DESC 
            LIMIT 5
        """
        rows = db.execute(text(sql)).mappings().all()
        print("\n--- ÚLTIMAS 5 TABELAS CRIADAS ---")
        for r in rows:
            print(dict(r))
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_recent_prices()
