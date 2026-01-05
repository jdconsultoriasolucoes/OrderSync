from sqlalchemy import text
import sys, os
# sys.path.append(os.getcwd()) # Not needed if running from backend dir
from database import SessionLocal

db = SessionLocal()
try:
    print("--- Checking Tabela Preco Data ---")
    sql = text("""
        SELECT 
            p.id_pedido, 
            p.tabela_preco_id,
            t.id_tabela,
            t.nome_tabela 
        FROM public.tb_pedidos p
        JOIN public.tb_tabela_preco t ON p.tabela_preco_id = t.id_tabela
        ORDER BY p.created_at DESC
        LIMIT 10
    """)
    rows = db.execute(sql).fetchall()
    if not rows:
        print("No rows found with JOIN.")
    for r in rows:
        print(f"Pedido: {r.id_pedido}, TabID: {r.tabela_preco_id}, NomeTabela: '{r.nome_tabela}'")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
