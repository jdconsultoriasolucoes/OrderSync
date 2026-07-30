import psycopg2

PROD_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
DEV_URL = "postgresql://jd_user:t6jq47rYatvkaKm5qmfV9suLolgz8shY@dpg-d9k6b8m417fc73e8mkhg-a.oregon-postgres.render.com/ordersync_dev"

def test_conn(url, name):
    print(f"--- Testando {name} ---")
    for ssl_mode in ["require", "allow", "prefer", "disable"]:
        try:
            conn = psycopg2.connect(url + f"?sslmode={ssl_mode}")
            cursor = conn.cursor()
            cursor.execute("SELECT current_database();")
            res = cursor.fetchone()
            print(f"SUCESSO com sslmode={ssl_mode}! DB: {res[0]}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Falha sslmode={ssl_mode}: {e}")
    return False

test_conn(PROD_URL, "PROD")
test_conn(DEV_URL, "DEV")
