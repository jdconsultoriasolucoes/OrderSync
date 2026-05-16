import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- VERIFICANDO DADOS DE COMISSÃO EM CLIENTES ALEATÓRIOS ---")
    cur.execute('''
        SELECT cadastro_codigo_da_empresa, cadastro_nome_cliente, comissao_insumos, comissao_pet 
        FROM t_cadastro_cliente_v2 
        LIMIT 10
    ''')
    for row in cur.fetchall():
        print(f"Cód: {row[0]} | Nome: {row[1]} | Insumos: '{row[2]}' | Pet: '{row[3]}'")
        
    conn.close()
except Exception as e:
    print(e)
