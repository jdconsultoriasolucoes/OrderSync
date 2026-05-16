import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 't_cadastro_cliente_v2_backup_2804'")
    exists = cur.fetchone()
    if exists:
        print("A tabela de backup existe.")
        cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2_backup_2804")
        print(f"Registros no backup: {cur.fetchone()[0]}")
    else:
        print("A tabela de backup NÃO existe.")
        
    conn.close()
except Exception as e:
    print(e)
