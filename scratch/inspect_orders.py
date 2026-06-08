import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

def inspect():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        # Pega 3 pedidos históricos com frete
        cur.execute("""
            SELECT id_pedido, usar_valor_com_frete, total_sem_frete, total_com_frete, total_pedido, frete_total, valor_frete_to, peso_total_kg
            FROM public.tb_pedidos
            WHERE total_sem_frete = 0 AND total_com_frete > 0 AND usar_valor_com_frete = True
            LIMIT 3;
        """)
        pedidos = cur.fetchall()
        print("--- PEDIDOS ENCONTRADOS ---")
        for p in pedidos:
            pid = p[0]
            print(f"Pedido ID: {pid} | usar_com_frete: {p[1]} | total_sem_f: {p[2]} | total_com_f: {p[3]} | total_pedido: {p[4]} | frete_total: {p[5]} | valor_frete_to: {p[6]} | peso_total_kg: {p[7]}")
            
            # Pega itens desse pedido
            cur.execute("""
                SELECT i.id_item, i.codigo, i.nome, i.quantidade, i.preco_unit, i.preco_unit_frt, i.subtotal_sem_f, i.subtotal_com_f, i.valor_frete_to, pr.peso, pr.peso_bruto
                FROM public.tb_pedidos_itens i
                LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
                WHERE i.id_pedido = %s;
            """, (pid,))
            itens = cur.fetchall()
            for it in itens:
                print(f"  -> Item: {it[1]} | {it[2][:20]} | Qtd: {it[3]} | unit_s: {it[4]} | unit_c: {it[5]} | sub_sem: {it[6]} | sub_com: {it[7]} | frete_to: {it[8]} | peso: {it[9]} | peso_bruto: {it[10]}")
            print("-" * 50)
            
    except Exception as e:
        print("Erro:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    inspect()
