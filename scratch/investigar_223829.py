import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- INVESTIGANDO CLIENTE 223829 ---")
    cur.execute("SELECT faturamento_municipio FROM tb_ingestao_clientes_2804 WHERE cadastro_codigo_da_empresa = '223829'")
    res = cur.fetchone()
    if res:
        cidade = res[0]
        print(f"Cidade do cliente 223829: '{cidade}'")
        
        cur.execute(f"SELECT * FROM tb_cidade_supervisor WHERE cidades ILIKE %s", (cidade,))
        sup_data = cur.fetchall()
        print(f"Dados na tb_cidade_supervisor para esta cidade: {sup_data}")
    else:
        print("Cliente 223829 não encontrado na ingestão.")
        
    conn.close()
except Exception as e:
    print(e)
