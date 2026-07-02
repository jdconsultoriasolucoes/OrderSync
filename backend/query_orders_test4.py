import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    print('--- Buscando Pedido 110305 ---')
    cur.execute('''SELECT * FROM tb_pedidos WHERE id_pedido = 110305;''')
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    for i, c in enumerate(cols): print(f'{c}: {row[i]}')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
