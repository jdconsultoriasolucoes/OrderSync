import psycopg2

urls = [
    ("PROD User Provided", "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"),
    ("DEV User Provided", "postgresql://jd_user:t6jq47rYatvkaKm5qmfV9suLolgz8shY@dpg-d9k6b8m417fc73e8mkhg-a.oregon-postgres.render.com/ordersync_dev?sslmode=require"),
    ("DB_WORK_GNGO", "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require"),
    ("ORDERSYNC_DB", "postgresql://ordersync_db_user:E0P2m6x1I8v7mX9uE4V7s1A6i3U8v2@dpg-cuid6n9u0jms73ep37gg-a.oregon-postgres.render.com/ordersync_db?sslmode=require"),
]

for label, url in urls:
    print(f"\n--- Testando {label} ---")
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT current_database(), count(*) FROM information_schema.tables WHERE table_schema='public';")
        db, count = cur.fetchone()
        print(f"CONECTADO COM SUCESSO! DB: {db} | Total Tabelas Public: {count}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERRO: {e}")
