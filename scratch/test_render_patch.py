import requests

PROD_TOKEN = "rnd_OkB6sCYcFSLW1Ql60qeRYxsSJfyQ"
PROD_ID = "dpg-d4781ehr0fns73f9ipc0-a"
my_ip = "187.56.172.138"

headers = {
    "Authorization": f"Bearer {PROD_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

payload = [
    { "cidrBlock": "179.181.151.38/32", "description": "edson.dispet@gmail.com" },
    { "cidrBlock": "179.113.161.85/32", "description": "edson.dispet@gmail.com" },
    { "cidrBlock": f"{my_ip}/32", "description": "Temporary migration access" }
]

methods = [
    ("PATCH", f"https://api.render.com/v1/postgres/{PROD_ID}", {"ipAllowList": payload}),
    ("PUT", f"https://api.render.com/v1/postgres/{PROD_ID}/ip-allow-list", payload),
    ("POST", f"https://api.render.com/v1/postgres/{PROD_ID}/ip-allow-list", payload),
]

for method, url, body in methods:
    print(f"Testing {method} {url}...")
    res = requests.request(method, url, headers=headers, json=body)
    print(f"Status: {res.status_code} | Text: {res.text[:200]}")
