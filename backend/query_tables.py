import psycopg2
conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tb_pedidos'")
cols = [r[0] for r in cur.fetchall()]
print("Columns in tb_pedidos:", cols)

cur.execute("SELECT * FROM tb_pedidos WHERE id_pedido=110300")
row = cur.fetchone()
if row:
    print("Order details:", dict(zip([desc[0] for desc in cur.description], row)))
