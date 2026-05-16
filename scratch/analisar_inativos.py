import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- AMOSTRA DE CLIENTES INATIVOS ---")
    
    # Selecionando 10 clientes inativos para ver os detalhes
    cur.execute('''
        SELECT cadastro_codigo_da_empresa, cadastro_nome_cliente, obs_nao_compra_observacoes
        FROM t_cadastro_cliente_v2 
        WHERE cadastro_ativo = false
        LIMIT 10
    ''')
    
    rows = cur.fetchall()
    for row in rows:
        print(f"Código: {row[0]} | Nome: {row[1]} | Obs/Ocorrência: {row[2]}")
        
    conn.close()
except Exception as e:
    print(e)
