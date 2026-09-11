import psycopg2
conn=psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require')
cur=conn.cursor()
cur.execute("SELECT status FROM tb_pedidos WHERE status != 'FATURADO_SUPRA' LIMIT 1;")
res = cur.fetchone()
if res:
    val = res[0]
    print(repr(val))
cur.close()
conn.close()
