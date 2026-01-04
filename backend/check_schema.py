from sqlalchemy import text
from database import SessionLocal

db = SessionLocal()
try:
    print("--- Checking tb_pedidos Columns ---")
    sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_pedidos'")
    rows = db.execute(sql).fetchall()
    cols = [r[0] for r in rows]
    print(cols)
    if 'tabela_preco_nome' in cols:
        print("CONFIRMED: tabela_preco_nome exists in tb_pedidos")
        # Check if it has data
        check_data = text("SELECT COUNT(*) FROM tb_pedidos WHERE tabela_preco_nome IS NOT NULL AND tabela_preco_nome != ''")
        cnt = db.execute(check_data).scalar()
        print(f"Rows with non-empty tabela_preco_nome: {cnt}")
    else:
        print("tabela_preco_nome DOES NOT EXIST in tb_pedidos")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
