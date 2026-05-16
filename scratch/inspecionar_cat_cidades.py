import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- CONTEÚDO DA TB_CIDADE_SUPERVISOR ---")
    cur.execute("SELECT * FROM tb_cidade_supervisor LIMIT 50")
    cols = [desc[0] for desc in cur.description]
    for row in cur.fetchall():
        print(dict(zip(cols, row)))
        
    conn.close()
except Exception as e:
    print(e)
