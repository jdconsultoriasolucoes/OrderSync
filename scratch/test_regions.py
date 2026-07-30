import psycopg2

user_pass_db = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@"
regions = ["oregon", "frankfurt", "singapore", "ohio", "virginia"]

for r in regions:
    url = f"{user_pass_db}dpg-d4781ehr0fns73f9ipc0-a.{r}-postgres.render.com/db_ordersync?sslmode=require"
    try:
        print(f"Testing region {r}...")
        conn = psycopg2.connect(url, connect_timeout=5)
        print(f"SUCCESS with region: {r}!")
        conn.close()
        break
    except Exception as e:
        print(f"Region {r} failed: {e}")
