import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    table_name = 't_cadastro_cliente_v2'
    cur.execute(f'''
        SELECT column_name, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' AND column_name = 'id'
    ''')
    print(f"Propriedades da coluna id em {table_name}:")
    print(cur.fetchone())
    
    conn.close()
except Exception as e:
    print(e)
