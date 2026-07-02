import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    print('--- Buscando 125423 ---')
    cur.execute('''SELECT cadastro_codigo_da_empresa, cadastro_nome_cliente FROM t_cadastro_cliente_v2 WHERE cadastro_codigo_da_empresa = '125423';''')
    rows = cur.fetchall()
    for r in rows: print(r)

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
