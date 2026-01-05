from sqlalchemy import text
from database import SessionLocal

db = SessionLocal()
try:
    print("--- Checking Tabela 4 ---")
    # First, confirm Order 204 tabela_id
    sql_ord = text("SELECT tabela_preco_id FROM public.tb_pedidos WHERE id_pedido = 204")
    tid = db.execute(sql_ord).scalar()
    print(f"Order 204 has Tabela ID: {tid}")

    if tid:
        sql_tab = text("SELECT * FROM public.tb_tabela_preco WHERE id_tabela = :tid")
        row = db.execute(sql_tab, {"tid": tid}).mappings().first()
        if row:
            print(f"Tabela Found: {dict(row)}")
        else:
            print("Tabela NOT FOUND.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
