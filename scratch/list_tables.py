import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    ''')
    
    print("Tabelas encontradas no banco:")
    for row in cur.fetchall():
        print(f" - {row[0]}")
            
    conn.close()
except Exception as e:
    print(e)
