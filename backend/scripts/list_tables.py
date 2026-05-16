import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def list_tables():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    tables = [r[0] for r in cur.fetchall()]
    print("Tabelas encontradas:")
    for t in tables:
        print(f"- {t}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_tables()
