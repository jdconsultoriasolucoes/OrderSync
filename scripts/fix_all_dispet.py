import sys
import os
sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))
from database import SessionLocal
from sqlalchemy import text

def fix_all_dispet():
    db = SessionLocal()
    try:
        print("--- CORRIGINDO TODAS AS TABELAS DISPET ---")
        
        # Select for audit
        audit_sql = """
            SELECT count(*) as qtd
            FROM tb_tabela_preco
            WHERE (cliente ILIKE '%DISPET%' OR nome_tabela ILIKE '%DISPET%')
              AND (codigo_cliente IS NULL OR codigo_cliente = '' OR codigo_cliente = 'Não cadastrado')
        """
        count = db.execute(text(audit_sql)).scalar()
        print(f"Encontradas {count} tabelas da DISPET sem código.")
        
        if count > 0:
            update_sql = """
                UPDATE tb_tabela_preco
                SET codigo_cliente = '132768'
                WHERE (cliente ILIKE '%DISPET%' OR nome_tabela ILIKE '%DISPET%')
                AND (codigo_cliente IS NULL OR codigo_cliente = '' OR codigo_cliente = 'Não cadastrado')
            """
            db.execute(text(update_sql))
            db.commit()
            print("✅ Atualização concluída.")
        else:
            print("Nada a atualizar.")

    except Exception as e:
        print(f"Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_dispet()
