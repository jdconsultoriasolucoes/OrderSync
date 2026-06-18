import psycopg2

conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tb_pedidos' AND column_name = 'codigo_cliente'")
print('tb_pedidos.codigo_cliente:', cur.fetchone())

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_cadastro_cliente_v2' AND column_name = 'cadastro_codigo_da_empresa'")
print('t_cadastro_cliente_v2.cadastro_codigo_da_empresa:', cur.fetchone())

cur.close()
conn.close()
