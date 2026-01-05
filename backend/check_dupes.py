from sqlalchemy import create_engine, text
import os
import sys
sys.path.append(os.getcwd())
from database import SessionLocal

db = SessionLocal()
try:
    print("Verificando duplicidades no JOIN de pedidos...")
    # Checa se algum pedido aparece mais de uma vez no JOIN com tabela de preço
    sql = text("""
        SELECT a.id_pedido, COUNT(*)
        FROM public.tb_pedidos a
        LEFT JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
        GROUP BY a.id_pedido
        HAVING COUNT(*) > 1
        LIMIT 10;
    """)
    res = db.execute(sql).fetchall()
    if res:
        print("DUPLICIDADES ENCONTRADAS! ID_PEDIDO | COUNT")
        for r in res:
            print(f"{r[0]} | {r[1]}")
    else:
        print("Nenhuma duplicidade encontrada no JOIN.")

    print("\nVerificando total de pedidos:")
    total = db.execute(text("SELECT COUNT(*) FROM tb_pedidos")).scalar()
    print(f"Total na tb_pedidos: {total}")

except Exception as e:
    print(f"Erro: {e}")
finally:
    db.close()
