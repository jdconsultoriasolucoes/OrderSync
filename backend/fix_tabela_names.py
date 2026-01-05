from sqlalchemy import text
from database import SessionLocal

db = SessionLocal()
try:
    print("--- Backfilling tabela_preco_nome for existing orders ---")
    
    # Update orders where tabela_preco_nome is NULL or empty, based on tb_tabela_preco
    sql = text("""
        UPDATE public.tb_pedidos p
           SET tabela_preco_nome = t.nome_tabela
          FROM public.tb_tabela_preco t
         WHERE p.tabela_preco_id = t.id_tabela
           AND (p.tabela_preco_nome IS NULL OR p.tabela_preco_nome = '')
    """)
    
    result = db.execute(sql)
    db.commit()
    print(f"Updated {result.rowcount} rows with missing table names.")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
