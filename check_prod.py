import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT * FROM t_cadastro_produto_v2 WHERE codigo_supra = '950CF12*0.5'")
row = cur.fetchone()
if row:
    colnames = [desc[0] for desc in cur.description]
    print(dict(zip(colnames, row)))
else:
    print('Product not found!')
