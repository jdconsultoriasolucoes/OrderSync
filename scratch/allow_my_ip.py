import requests
import json
import psycopg2

PROD_TOKEN = "rnd_OkB6sCYcFSLW1Ql60qeRYxsSJfyQ"
PROD_ID = "dpg-d4781ehr0fns73f9ipc0-a"
PROD_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

my_ip = "187.56.172.138"

headers = {
    "Authorization": f"Bearer {PROD_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Add IP
new_allow_list = [
    { "cidrBlock": "179.181.151.38/32", "description": "edson.dispet@gmail.com" },
    { "cidrBlock": "179.113.161.85/32", "description": "edson.dispet@gmail.com" },
    { "cidrBlock": f"{my_ip}/32", "description": "Temporary migration access" }
]

print("Atualizando IP Allow List no Render...")
res = requests.put(f"https://api.render.com/v1/postgres/{PROD_ID}", headers=headers, json={"ipAllowList": new_allow_list})
print(f"Status Render API: {res.status_code}")
if res.status_code in (200, 201, 202):
    print("IP liberado com sucesso no Render!")
else:
    print(f"Erro no Render API: {res.text}")

print("\nTestando conexão com o Banco PROD...")
try:
    conn = psycopg2.connect(PROD_URL, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT current_database(), count(*) FROM information_schema.tables WHERE table_schema='public';")
    db, count = cur.fetchone()
    print(f"CONECTADO COM SUCESSO AO PROD! DB: {db} | Total Tabelas Public: {count}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"ERRO DE CONEXAO PROD: {e}")
