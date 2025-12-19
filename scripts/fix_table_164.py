import sys
import os
sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))
from database import SessionLocal
from sqlalchemy import text

def fix_table_164():
    db = SessionLocal()
    try:
        print("--- CORRIGINDO TABELA 164 ---")
        # 1. Verify it is indeed DISPET (or check name)
        check = db.execute(text("SELECT nome_tabela, cliente FROM tb_tabela_preco WHERE id_tabela = 164 LIMIT 1")).mappings().first()
        if not check:
            print("Tabela 164 não encontrada.")
            return
            
        print(f"Tabela encontrada: {dict(check)}")
        
        # 2. Update code
        # We also look for other tables with 'DISPET' and missing code to fix them en-masse? 
        # For now, safe approach: just 164.
        
        sql = """
            UPDATE tb_tabela_preco
            SET codigo_cliente = '132768'
            WHERE id_tabela = 164
        """
        db.execute(text(sql))
        db.commit()
        print("✅ Tabela 164 atualizada com codigo_cliente = '132768'")
        
        # Verify
        check_after = db.execute(text("SELECT codigo_cliente FROM tb_tabela_preco WHERE id_tabela = 164 LIMIT 1")).scalar()
        print(f"Verificação pós-update: codigo_cliente = {check_after}")

    except Exception as e:
        print(f"Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_table_164()
