import psycopg2
DSN = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
def check_cols():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_pedidos_itens'")
    rows = cur.fetchall()
    print([r[0] for r in rows])
    cur.close()
    conn.close()
if __name__ == "__main__":
    check_cols()
