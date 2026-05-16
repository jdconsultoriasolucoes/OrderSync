import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- PASSO 1: CRIANDO BACKUP DEFINITIVO ---")
    backup_table = "t_cadastro_cliente_v2_backup_2804"
    cur.execute(f"DROP TABLE IF EXISTS {backup_table}")
    cur.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM t_cadastro_cliente_v2")
    conn.commit() # Commit do backup garantido
    print(f"Backup criado com sucesso na tabela {backup_table}.")
    
    print("--- PASSO 2: LIMPANDO TABELA OFICIAL ---")
    cur.execute("TRUNCATE TABLE t_cadastro_cliente_v2 CASCADE")
    conn.commit()
    print("Tabela t_cadastro_cliente_v2 limpa.")
    
    print("--- PASSO 3: MIGRANDO DADOS DA INGESTÃO ---")
    # Agora incluímos o ID na lista de colunas
    cur.execute('''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 't_cadastro_cliente_v2'
        ORDER BY ordinal_position
    ''')
    columns = [row[0] for row in cur.fetchall()]
    cols_str = ", ".join([f'"{c}"' for c in columns])
    
    insert_query = f'''
        INSERT INTO t_cadastro_cliente_v2 ({cols_str})
        SELECT {cols_str} FROM tb_ingestao_clientes_2804
    '''
    cur.execute(insert_query)
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2")
    count_final = cur.fetchone()[0]
    print(f"Migração concluída com sucesso! Total de registros: {count_final}")
    
    conn.close()
except Exception as e:
    print(f"ERRO: {e}")
    if 'conn' in locals() and conn:
        conn.rollback()
        conn.close()
