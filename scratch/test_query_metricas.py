import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def test_query():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        query = """
            SELECT 
                EXTRACT(YEAR FROM COALESCE(criado_em, created_at))::INTEGER AS ano,
                EXTRACT(MONTH FROM COALESCE(criado_em, created_at))::INTEGER AS mes,
                COUNT(*) AS total_pedidos,
                ROUND(SUM(peso_total_kg), 2) AS peso_total_kg,
                ROUND(SUM(total_pedido), 2) AS valor_total
            FROM public.tb_pedidos
            GROUP BY ano, mes
            ORDER BY ano DESC, mes DESC;
        """
        cur.execute(query)
        res = cur.fetchall()
        print("=== RESULTADOS DA QUERY ===")
        for r in res[:10]: # Print top 10 rows
            print(f"Ano: {r[0]} | Mês: {r[1]} | Qtd Pedidos: {r[2]} | Peso Total (kg): {r[3]} | Valor Total (R$): {r[4]}")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    test_query()
