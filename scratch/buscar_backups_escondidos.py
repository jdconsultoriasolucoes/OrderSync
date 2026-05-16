import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name ILIKE '%backup%' 
       OR table_name ILIKE '%bkp%' 
       OR table_name ILIKE '%copy%' 
       OR table_name ILIKE '%old%'
       OR table_name ILIKE '%temp%'
    """
    cur.execute(query)
    tables = cur.fetchall()
    
    print("Tabelas de backup/temporárias encontradas:")
    for t in tables:
        print(f" - {t[0]}")
        
    conn.close()
except Exception as e:
    print(e)
