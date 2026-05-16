import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- RELATÓRIO DE CRUZAMENTO DE CLIENTES ---")
    
    # 1. Clientes novos (baseado em código da empresa)
    cur.execute('''
        SELECT COUNT(*) 
        FROM tb_ingestao_clientes_2804 i
        LEFT JOIN t_cadastro_cliente_v2 c ON i.cadastro_codigo_da_empresa = c.cadastro_codigo_da_empresa
        WHERE c.cadastro_codigo_da_empresa IS NULL
    ''')
    novos = cur.fetchone()[0]
    print(f"Novos Clientes (não encontrados no sistema): {novos}")
    
    # 2. Clientes existentes
    cur.execute('''
        SELECT COUNT(*) 
        FROM tb_ingestao_clientes_2804 i
        INNER JOIN t_cadastro_cliente_v2 c ON i.cadastro_codigo_da_empresa = c.cadastro_codigo_da_empresa
    ''')
    existentes = cur.fetchone()[0]
    print(f"Clientes já existentes no sistema: {existentes}")
    
    # 3. Diferença de status (Ativo/Inativo)
    cur.execute('''
        SELECT COUNT(*) 
        FROM tb_ingestao_clientes_2804 i
        INNER JOIN t_cadastro_cliente_v2 c ON i.cadastro_codigo_da_empresa = c.cadastro_codigo_da_empresa
        WHERE i.cadastro_ativo != c.cadastro_ativo
    ''')
    dif_status = cur.fetchone()[0]
    print(f"Clientes com divergência de Status (Ativo/Inativo): {dif_status}")
    
    conn.close()
except Exception as e:
    print(f"Erro ao cruzar dados: {e}")
