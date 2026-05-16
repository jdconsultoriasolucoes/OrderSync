import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- ANÁLISE DE STATUS DOS CLIENTES IMPORTADOS ---")
    
    cur.execute('''
        SELECT cadastro_ativo, COUNT(*) 
        FROM t_cadastro_cliente_v2 
        GROUP BY cadastro_ativo
    ''')
    
    for row in cur.fetchall():
        status = "Ativo" if row[0] else "Inativo"
        print(f"Status {status}: {row[1]} clientes")
        
    cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2")
    print(f"Total Geral: {cur.fetchone()[0]}")
    
    conn.close()
except Exception as e:
    print(e)
