import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def normalize_city_sql(column):
    return f'''
        TRIM(UPPER(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    unaccent({column}), 
                    '\\s*\\([A-Z]{{2}}\\)', '', 'g'
                ), 
                '[^A-Z0-9]', ' ', 'g'
            )
        ))
    '''

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    
    print("--- INICIANDO ATUALIZAÇÃO COMPLETA DA ELABORAÇÃO ---")
    
    # 1. Atualizar Comissões e Dados de Perfil
    print("Passo 1: Atualizando comissões globais...")
    cur.execute("SELECT razao_social, codigo_representante FROM t_profile_config LIMIT 1")
    profile = cur.fetchone()
    if profile:
        razao, codigo = profile
        comissao_text = f"{razao.upper()} - CÓDIGO {codigo}" if codigo else razao.upper()
        cur.execute('''
            UPDATE t_cadastro_cliente_v2 
            SET comissao_insumos = %s, comissao_pet = %s
        ''', (comissao_text, comissao_text))
        print(f"Passo 1: Comissões atualizadas para {cur.rowcount} clientes: {comissao_text}")

    # 2. Atualizar Gerentes e Supervisores por Cidade
    print("Passo 2: Sincronizando Gerentes e Supervisores...")
    cur.execute(f'''
        UPDATE t_cadastro_cliente_v2 c
        SET 
            elaboracao_gerente_insumos = s.gerente_insumos,
            elaboracao_gerente_pet = s.gerente_pet,
            supervisor_codigo_insumo = CAST(s.numero_supervisor_insumos AS TEXT),
            supervisor_nome_insumo = s.nome_supervisor_insumos,
            supervisor_codigo_pet = CAST(s.numero_supervisor_pet AS TEXT),
            supervisor_nome_pet = s.nome_supervisor_pet
        FROM tb_cidade_supervisor s
        WHERE {normalize_city_sql('c.faturamento_municipio')} = {normalize_city_sql('s.cidades')}
    ''')
    print(f"{cur.rowcount} clientes atualizados com dados de Supervisor/Gerente.")

    # 3. Atualizar Rotas por Cidade
    print("Passo 3: Sincronizando Rotas...")
    cur.execute(f'''
        UPDATE t_cadastro_cliente_v2 c
        SET entrega_rota_principal = CAST(r.rota AS TEXT)
        FROM tb_municipio_rota r
        WHERE {normalize_city_sql('c.faturamento_municipio')} = {normalize_city_sql('r.municipio')}
    ''')
    print(f"Passo 3: {cur.rowcount} clientes atualizados com dados de Rota.")
    
    # 4. Atualizar Canais por Tipo de Cliente
    print("Passo 4: Sincronizando Canais de Venda...")
    cur.execute('''
        UPDATE t_cadastro_cliente_v2 c
        SET 
            canal_pet = (SELECT CAST("Id" AS TEXT) FROM tb_canal_venda cv WHERE cv.tipo = c.cadastro_tipo_cliente AND cv.linha = 'Pet' LIMIT 1),
            canal_insumos = (SELECT CAST("Id" AS TEXT) FROM tb_canal_venda cv WHERE cv.tipo = c.cadastro_tipo_cliente AND cv.linha = 'Insumos' LIMIT 1),
            canal_frost = (SELECT CAST("Id" AS TEXT) FROM tb_canal_venda cv WHERE cv.tipo = c.cadastro_tipo_cliente AND cv.linha = 'Frost' LIMIT 1)
        WHERE cadastro_tipo_cliente IS NOT NULL
    ''')
    print(f"Passo 4: {cur.rowcount} clientes atualizados com códigos de Canal.")

    conn.commit()
    print("--- ATUALIZAÇÃO CONCLUÍDA COM SUCESSO ---")
    
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
    if 'conn' in locals() and conn:
        conn.rollback()
        conn.close()
