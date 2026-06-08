import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

def check_product():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, nome_produto, peso, peso_bruto, codigo_supra 
            FROM public.t_cadastro_produto_v2 
            WHERE codigo_supra = '535E825';
        """)
        rows = cur.fetchall()
        print("id | nome | peso | peso_bruto | codigo_supra")
        print("-" * 80)
        for r in rows:
            print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")
            
    except Exception as e:
        print("Erro:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    check_product()
