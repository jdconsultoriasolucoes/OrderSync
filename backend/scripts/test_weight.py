import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
from sqlalchemy import text

def test_weight():
    sql = text("""
        SELECT 
            a.id_pedido,
            (
                SELECT COALESCE(SUM(i.quantidade * COALESCE(prod.peso, 0)), 0)
                FROM tb_pedidos_itens i
                LEFT JOIN (
                    SELECT codigo_supra, MAX(peso) as peso 
                    FROM t_cadastro_produto_v2 
                    GROUP BY codigo_supra
                ) prod ON prod.codigo_supra = i.codigo
                WHERE i.id_pedido = a.id_pedido
            ) AS peso_liquido_calculado
        FROM public.tb_pedidos a
        ORDER BY a.id_pedido DESC
        LIMIT 5
    """)
    for attempt in range(5):
        try:
            with SessionLocal() as db:
                rows = db.execute(sql).mappings().all()
                for r in rows:
                    print(f"Pedido {r['id_pedido']}: Peso Líquido Calculado = {r['peso_liquido_calculado']}")
                return
        except Exception as e:
            print(f"Erro na tentativa {attempt+1}: {e}")
            time.sleep(2)
            
if __name__ == "__main__":
    test_weight()
