import psycopg2

conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    print("--- BUSCANDO TODAS AS CIDADES NA TB_CIDADE_SUPERVISOR ---")
    cur.execute("SELECT cidades, nome_supervisor_insumos, nome_supervisor_pet FROM tb_cidade_supervisor ORDER BY cidades")
    for row in cur.fetchall():
        print(f"Cidade: '{row[0]}' | Ins: '{row[1]}' | Pet: '{row[2]}'")
        
    conn.close()
except Exception as e:
    print(e)
