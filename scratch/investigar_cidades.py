import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- AMOSTRA DE CIDADES EM CLIENTES ---")
    cur.execute("SELECT DISTINCT faturamento_municipio FROM t_cadastro_cliente_v2 LIMIT 10")
    for row in cur.fetchall():
        print(f" Cliente: '{row[0]}'")
        
    print("\n--- AMOSTRA DE CIDADES EM ROTAS ---")
    cur.execute("SELECT DISTINCT municipio FROM tb_municipio_rota LIMIT 10")
    for row in cur.fetchall():
        print(f" Rota: '{row[0]}'")
        
    conn.close()
except Exception as e:
    print(e)
