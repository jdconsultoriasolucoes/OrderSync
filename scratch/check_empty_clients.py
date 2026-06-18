import psycopg2

conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2 WHERE cadastro_codigo_da_empresa::text = ''")
empty_count = cur.fetchone()[0]
print("Empty string codes:", empty_count)

cur.execute("SELECT COUNT(*) FROM t_cadastro_cliente_v2 WHERE cadastro_codigo_da_empresa IS NULL")
null_count = cur.fetchone()[0]
print("NULL codes:", null_count)

cur.close()
conn.close()
