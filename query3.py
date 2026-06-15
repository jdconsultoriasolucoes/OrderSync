import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT atualizado_em, created_at, pedido_supra FROM tb_pedidos WHERE id_pedido = 109996;")
print('Atualizado em:', cur.fetchall())
