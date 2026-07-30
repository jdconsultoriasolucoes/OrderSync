import requests

PROD_TOKEN = "rnd_OkB6sCYcFSLW1Ql60qeRYxsSJfyQ"
PROD_ID = "dpg-d4781ehr0fns73f9ipc0-a"

headers = {
    "Authorization": f"Bearer {PROD_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Restore original IP allow list
original_allow_list = [
    { "cidrBlock": "179.181.151.38/32", "description": "edson.dispet@gmail.com" },
    { "cidrBlock": "179.113.161.85/32", "description": "edson.dispet@gmail.com" }
]

print("Restaurando IP Allow List de PROD para a lista original...")
res = requests.patch(f"https://api.render.com/v1/postgres/{PROD_ID}", headers=headers, json={"ipAllowList": original_allow_list})
print(f"Status Render API: {res.status_code}")
if res.status_code == 200:
    print("PROD IP Allow List restaurada com sucesso ao estado de segurança original!")
else:
    print(f"Aviso: {res.text}")
