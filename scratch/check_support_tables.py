import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    tables = ['tb_cidade_supervisor', 'tb_municipio_rota', 't_profile_config']
    for t in tables:
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'")
        print(f"Table: {t}")
        for row in cur.fetchall():
            print(f"  {row[0]} ({row[1]})")
            
    conn.close()
except Exception as e:
    print(e)
