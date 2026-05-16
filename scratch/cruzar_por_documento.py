import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def normalize_sql(column):
    return f"REGEXP_REPLACE({column}, '[^0-9]', '', 'g')"

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- ANÁLISE DE CRUZAMENTO POR CNPJ/CPF (REFINADA) ---")
    
    # 1. Cruzamento por CNPJ (Apenas válidos)
    query_cnpj = f'''
        SELECT COUNT(DISTINCT i.id) 
        FROM tb_ingestao_clientes_2804 i
        INNER JOIN t_cadastro_cliente_v2 c ON {normalize_sql('i.cadastro_cnpj')} = {normalize_sql('c.cadastro_cnpj')}
        WHERE {normalize_sql('i.cadastro_cnpj')} != '' 
          AND {normalize_sql('i.cadastro_cnpj')} IS NOT NULL 
          AND {normalize_sql('i.cadastro_cnpj')} NOT IN ('00000000000000', '11111111111111')
    '''
    cur.execute(query_cnpj)
    existentes_cnpj = cur.fetchone()[0]
    
    # 2. Cruzamento por CPF (Apenas válidos)
    query_cpf = f'''
        SELECT COUNT(DISTINCT i.id) 
        FROM tb_ingestao_clientes_2804 i
        INNER JOIN t_cadastro_cliente_v2 c ON {normalize_sql('i.cadastro_cpf')} = {normalize_sql('c.cadastro_cpf')}
        WHERE {normalize_sql('i.cadastro_cpf')} != '' 
          AND {normalize_sql('i.cadastro_cpf')} IS NOT NULL 
          AND {normalize_sql('i.cadastro_cpf')} NOT IN ('00000000000', '11111111111')
    '''
    cur.execute(query_cpf)
    existentes_cpf = cur.fetchone()[0]
    
    # 3. Total único de existentes por documento (CNPJ ou CPF)
    query_total_unico = f'''
        SELECT COUNT(DISTINCT i.id) 
        FROM tb_ingestao_clientes_2804 i
        INNER JOIN t_cadastro_cliente_v2 c ON (
            ({normalize_sql('i.cadastro_cnpj')} = {normalize_sql('c.cadastro_cnpj')} AND {normalize_sql('i.cadastro_cnpj')} NOT IN ('', '00000000000000'))
            OR 
            ({normalize_sql('i.cadastro_cpf')} = {normalize_sql('c.cadastro_cpf')} AND {normalize_sql('i.cadastro_cpf')} NOT IN ('', '00000000000'))
        )
    '''
    cur.execute(query_total_unico)
    total_existentes = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tb_ingestao_clientes_2804")
    total_ingestao = cur.fetchone()[0]
    novos = total_ingestao - total_existentes
    
    print(f"Total de registros na Ingestão: {total_ingestao}")
    print(f"Clientes existentes (CNPJ): {existentes_cnpj}")
    print(f"Clientes existentes (CPF): {existentes_cpf}")
    print(f"Total únicos encontrados por Documento: {total_existentes}")
    print(f"Novos clientes (por Documento): {novos}")
    
    print("\n--- ANÁLISE DE CÓDIGO DA EMPRESA ---")
    
    # 4. Registros sem código da empresa
    cur.execute('''
        SELECT COUNT(*) 
        FROM tb_ingestao_clientes_2804 
        WHERE cadastro_codigo_da_empresa IS NULL OR cadastro_codigo_da_empresa = '' OR cadastro_codigo_da_empresa = 'None' OR cadastro_codigo_da_empresa = 'nan'
    ''')
    sem_codigo = cur.fetchone()[0]
    print(f"Registros sem Código da Empresa na Ingestão: {sem_codigo}")
    
    # 5. Desses sem código, quantos já existem no sistema (por documento)
    query_sem_codigo_existentes = f'''
        SELECT COUNT(DISTINCT i.id) 
        FROM tb_ingestao_clientes_2804 i
        INNER JOIN t_cadastro_cliente_v2 c ON (
            ({normalize_sql('i.cadastro_cnpj')} = {normalize_sql('c.cadastro_cnpj')} AND {normalize_sql('i.cadastro_cnpj')} NOT IN ('', '00000000000000'))
            OR 
            ({normalize_sql('i.cadastro_cpf')} = {normalize_sql('c.cadastro_cpf')} AND {normalize_sql('i.cadastro_cpf')} NOT IN ('', '00000000000'))
        )
        WHERE i.cadastro_codigo_da_empresa IS NULL OR i.cadastro_codigo_da_empresa = '' OR i.cadastro_codigo_da_empresa = 'None' OR i.cadastro_codigo_da_empresa = 'nan'
    '''
    cur.execute(query_sem_codigo_existentes)
    sem_codigo_ja_existem = cur.fetchone()[0]
    print(f"Registros sem código que JÁ EXISTEM no sistema (por Doc): {sem_codigo_ja_existem}")

    conn.close()
except Exception as e:
    print(f"Erro: {e}")
