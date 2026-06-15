import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT importado_em, status_processamento FROM tb_pedidos_importados WHERE pedido_supra = '2026002992' ORDER BY importado_em DESC LIMIT 5;")
print('Logs importados (2026002992):', cur.fetchall())
cur.execute("SELECT id_pedido, created_at, atualizado_em, pedido_supra FROM tb_pedidos WHERE pedido_supra = '2026002992';")
print('Pedido atual (2026002992):', cur.fetchall())
