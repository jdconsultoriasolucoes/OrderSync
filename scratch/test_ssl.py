import psycopg2
import ssl

url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    print("Testing connection with custom ssl context...")
    conn = psycopg2.connect(
        url,
        sslmode='require',
        connect_timeout=15
    )
    print("CONNECTED SUCCESSFULLY!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
