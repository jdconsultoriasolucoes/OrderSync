import sys
import os
# Add backend to path so we can import 'database'
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import SessionLocal
from sqlalchemy import text

def check_duplicates():
    db = SessionLocal()
    try:
        print("--- Checking Order #267 Items ---")
        sql_items = text("""
            SELECT id_item, id_pedido, codigo, quantidade
            FROM tb_pedidos_itens
            WHERE id_pedido = 267
        """)
        items = db.execute(sql_items).fetchall()
        print(f"Items found: {len(items)}")
        codes_in_order = []
        for i in items:
            print(i)
            codes_in_order.append(i.codigo)
            
        print("\n--- Checking t_cadastro_produto_v2 duplicates (for order items) ---")
        if codes_in_order:
            codes_str = "', '".join(codes_in_order)
            sql = text(f"""
                SELECT codigo_supra, COUNT(*), array_agg(id), array_agg(status_produto)
                FROM t_cadastro_produto_v2
                WHERE codigo_supra IN ('{codes_str}')
                GROUP BY codigo_supra
                HAVING COUNT(*) > 1
            """)
            rows = db.execute(sql).fetchall()
            if rows:
                print("!!! FOUND DUPLICATES in Product Table !!!")
                for r in rows:
                    print(r)
            else:
                print("No duplicates found in Product Table for these items.")
        
        print("\n--- Checking tb_tabela_preco duplicates (for order items) ---")
        # We need to know which table is used.
        sql_order = text("SELECT tabela_preco_id FROM tb_pedidos WHERE id_pedido = 267")
        order_res = db.execute(sql_order).first()
        if order_res:
            tid = order_res[0]
            print(f"Order uses TabelaPreco ID: {tid}")
            if codes_in_order:
                sql_tp = text(f"""
                    SELECT codigo_produto_supra, id_tabela, COUNT(*), array_agg(ativo)
                    FROM tb_tabela_preco
                    WHERE id_tabela = {tid}
                      AND codigo_produto_supra IN ('{codes_str}')
                    GROUP BY codigo_produto_supra, id_tabela
                    HAVING COUNT(*) > 1
                """)
                rows_tp = db.execute(sql_tp).fetchall()
                if rows_tp:
                    print("!!! FOUND DUPLICATES in Price Table !!!")
                    for r in rows_tp:
                        print(r)
                else:
                    print("No duplicates found in Price Table for these items.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_duplicates()
