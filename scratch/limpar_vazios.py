import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- LIMPANDO REGISTROS VAZIOS ---")
    
    # Deletando registros onde o nome do cliente está vazio ou é 'nan'
    cur.execute('''
        DELETE FROM t_cadastro_cliente_v2 
        WHERE cadastro_nome_cliente IS NULL 
           OR cadastro_nome_cliente = '' 
           OR cadastro_nome_cliente = 'nan'
    ''')
    deletados = cur.rowcount
    print(f"Registros vazios removidos: {deletados}")
    
    cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2")
    total = cur.fetchone()[0]
    print(f"Total de clientes reais na tabela: {total}")
    
    cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2 WHERE cadastro_ativo = true")
    ativos = cur.fetchone()[0]
    print(f"Clientes Ativos: {ativos}")
    
    cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2 WHERE cadastro_ativo = false")
    inativos = cur.fetchone()[0]
    print(f"Clientes Inativos Reais: {inativos}")
    
    conn.commit()
    conn.close()
except Exception as e:
    print(e)
