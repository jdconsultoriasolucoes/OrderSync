import sys
import os
sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))
from database import SessionLocal
from sqlalchemy import text

def force_st_table_164():
    db = SessionLocal()
    try:
        print("--- FORÇANDO ST NA TABELA 164 ---")
        
        sql = """
            UPDATE tb_tabela_preco
            SET calcula_st = true
            WHERE id_tabela = 164
        """
        db.execute(text(sql))
        db.commit()
        print("✅ Tabela 164 atualizada com calcula_st = TRUE")
        
    except Exception as e:
        print(f"Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_st_table_164()
