import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT id_pedido, length(pedido_supra), pedido_supra FROM tb_pedidos WHERE id_pedido = 109996;")
print('Tamanho no tb_pedidos:', cur.fetchall())
cur.execute("SELECT id_importacao, length(pedido_supra), pedido_supra FROM tb_pedidos_importados WHERE id_importacao = 4393;")
print('Tamanho no importados:', cur.fetchall())
