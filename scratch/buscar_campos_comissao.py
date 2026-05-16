import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- BUSCANDO CAMPOS DE COMISSÃO ---")
    cur.execute('''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 't_cadastro_cliente_v2' 
          AND column_name ILIKE '%%comissao%%'
    ''')
    for row in cur.fetchall():
        print(f"Coluna encontrada: {row[0]}")
        
    conn.close()
except Exception as e:
    print(e)
