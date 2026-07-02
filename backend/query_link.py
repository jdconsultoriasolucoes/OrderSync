import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT * FROM tb_pedido_link WHERE code = 'V4e3ZTo4xxjHUCIs'")
cols = [desc[0] for desc in cur.description]
rows = cur.fetchall()
if rows:
    print([dict(zip(cols, row)) for row in rows])
else:
    print("No link entries found")
