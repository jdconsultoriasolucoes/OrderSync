
import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()

print('--- CHECKING TB_CARGAS MAX ID AND DUPLICATES ---')
cur.execute('SELECT id, numero_carga FROM tb_cargas ORDER BY id DESC LIMIT 10;')
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()

