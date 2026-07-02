import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    cur.execute('''SELECT tabela_preco_id FROM tb_pedidos WHERE id_pedido = 110310;''')
    tid = cur.fetchone()[0]
    cur.execute('SELECT id_tabela, nome_tabela, codigo_cliente, cliente FROM tb_tabela_preco WHERE id_tabela = %s;', (tid,))
    row = cur.fetchone()
    print(f'Tabela para 110310: {row}')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
