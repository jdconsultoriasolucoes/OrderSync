import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    table_name = 't_cadastro_cliente_v2'
    
    print(f"--- ANALISANDO DEPENDÊNCIAS DE {table_name} ---")
    
    # 1. Foreign Keys que APONTAM para esta tabela
    print("\n[1] Foreign Keys de outras tabelas que apontam para esta:")
    cur.execute(f"""
        SELECT
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = '{table_name}';
    """)
    fks_pointing = cur.fetchall()
    for fk in fks_pointing:
        print(f" - Tabela '{fk[0]}' coluna '{fk[1]}' aponta para {table_name}({fk[3]})")
    if not fks_pointing: print(" - Nenhuma encontrada.")

    # 2. Triggers
    print("\n[2] Triggers nesta tabela:")
    cur.execute(f"""
        SELECT trigger_name, event_manipulation, action_statement
        FROM information_schema.triggers
        WHERE event_object_table = '{table_name}';
    """)
    triggers = cur.fetchall()
    for tg in triggers:
        print(f" - Trigger: {tg[0]} | Evento: {tg[1]}")
    if not triggers: print(" - Nenhuma encontrada.")

    # 3. Sequences
    print("\n[3] Sequences associadas (importante para o ID):")
    cur.execute(f"""
        SELECT column_name, column_default 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' AND column_default LIKE 'nextval%';
    """)
    sequences = cur.fetchall()
    for seq in sequences:
        print(f" - Coluna '{seq[0]}' usa default: {seq[1]}")

    conn.close()
except Exception as e:
    print(e)
