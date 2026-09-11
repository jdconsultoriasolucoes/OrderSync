import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT status_produto, COUNT(*) FROM t_cadastro_produto_v2 GROUP BY status_produto")
for row in cur.fetchall():
    print(repr(row[0]), row[1])

# Fix them
cur.execute("UPDATE t_cadastro_produto_v2 SET status_produto = TRIM(status_produto)")
conn.commit()
print("Fixed!")
