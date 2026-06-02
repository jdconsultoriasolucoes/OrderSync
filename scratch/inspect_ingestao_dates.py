import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def inspect_ingestao_dates():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT count(*) FROM tb_pedidos_ingestao 
            WHERE created_at >= '2026-05-28 00:00:00-03'::timestamptz;
        """)
        count_gte = cur.fetchone()[0]
        print(f"Pedidos com created_at >= 28/05/2026 (UTC-3): {count_gte}")
        
        cur.execute("""
            SELECT count(*) FROM tb_pedidos_ingestao 
            WHERE created_at < '2026-05-28 00:00:00-03'::timestamptz;
        """)
        count_lt = cur.fetchone()[0]
        print(f"Pedidos com created_at < 28/05/2026 (UTC-3): {count_lt}")
        
        cur.execute("""
            SELECT min(created_at), max(created_at) FROM tb_pedidos_ingestao;
        """)
        min_date, max_date = cur.fetchone()
        print(f"Datas na tabela staging: min={min_date}, max={max_date}")
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    inspect_ingestao_dates()
