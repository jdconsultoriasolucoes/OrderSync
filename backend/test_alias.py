from sqlalchemy import text
from database import SessionLocal

db = SessionLocal()
try:
    print("--- Testing Listagem Alias ---")
    sql = text("""
        SELECT 
            p.id_pedido, 
            t.nome_tabela AS tabela_preco_nome
        FROM public.tb_pedidos p
        JOIN public.tb_tabela_preco t ON p.tabela_preco_id = t.id_tabela
        WHERE p.id_pedido = 204
    """)
    row = db.execute(sql).mappings().first()
    if row:
        print(f"Row Keys: {row.keys()}")
        print(f"Value for 'tabela_preco_nome': '{row['tabela_preco_nome']}'")
    else:
        print("Order 204 not found in Join query.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
