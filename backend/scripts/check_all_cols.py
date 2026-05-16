import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def check_all():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    tables = ['tb_pedidos']
    
    for t in tables:
        print(f"\n--- {t} ---")
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")
        cols = [r[0] for r in cur.fetchall()]
        print(cols)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_all()
