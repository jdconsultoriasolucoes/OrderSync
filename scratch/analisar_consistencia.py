import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- ANÁLISE DE CONSISTÊNCIA ---")
    
    cur.execute("SELECT COUNT(*) FROM tb_ingestao_clientes_2804")
    total = cur.fetchone()[0]
    print(f"Total de registros inseridos: {total}")
    
    cur.execute("SELECT COUNT(DISTINCT cadastro_codigo_da_empresa) FROM tb_ingestao_clientes_2804")
    unicos = cur.fetchone()[0]
    print(f"Códigos de empresa únicos: {unicos}")
    
    cur.execute("SELECT cadastro_codigo_da_empresa, COUNT(*) FROM tb_ingestao_clientes_2804 GROUP BY cadastro_codigo_da_empresa HAVING COUNT(*) > 1 LIMIT 5")
    duplicados = cur.fetchall()
    if duplicados:
        print(f"Exemplos de códigos duplicados: {duplicados}")
    
    cur.execute("SELECT cadastro_codigo_da_empresa FROM tb_ingestao_clientes_2804 LIMIT 5")
    print(f"Exemplos de códigos na ingestão: {cur.fetchall()}")

    cur.execute("SELECT cadastro_codigo_da_empresa FROM t_cadastro_cliente_v2 LIMIT 5")
    print(f"Exemplos de códigos no sistema: {cur.fetchall()}")
    
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
