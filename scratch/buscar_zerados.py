import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def buscar_zerados():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        # Buscar os itens que ficaram zerados
        cur.execute("""
            SELECT it.id_pedido, p.pedido_supra, it.codigo, it.nome, it.quantidade, it.peso_kg
            FROM public.tb_pedidos_itens it
            LEFT JOIN public.tb_pedidos p ON it.id_pedido = p.id_pedido
            WHERE it.peso_kg IS NULL OR it.peso_kg = 0
            ORDER BY it.id_pedido, it.codigo;
        """)
        itens = cur.fetchall()
        
        print("=== ITENS ZERADOS ===")
        for row in itens:
            print(f"PEDIDO_ID:{row[0]}|SUPRA:{row[1]}|CODIGO:{row[2]}|NOME:{row[3]}|QTD:{row[4]}|PESO:{row[5]}")
            
        # Buscar os pedidos que ficaram zerados
        cur.execute("""
            SELECT id_pedido, pedido_supra, cliente, peso_total_kg
            FROM public.tb_pedidos
            WHERE peso_total_kg IS NULL OR peso_total_kg = 0
            ORDER BY id_pedido;
        """)
        pedidos = cur.fetchall()
        
        print("\n=== PEDIDOS ZERADOS ===")
        for row in pedidos:
            print(f"PEDIDO_ID:{row[0]}|SUPRA:{row[1]}|CLIENTE:{row[2]}|PESO_TOTAL:{row[3]}")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    buscar_zerados()
