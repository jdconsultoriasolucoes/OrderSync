import requests

BASE_URL = "http://127.0.0.1:8000/api/dashboard"

endpoints = ["/geral", "/vendas", "/produtos", "/clientes", "/logistica", "/pivot"]

for ep in endpoints:
    try:
        r = requests.get(f"{BASE_URL}{ep}")
        print(f"[{r.status_code}] {ep}")
        if r.status_code != 200:
            print(r.text)
    except Exception as e:
        print(f"Failed to connect to backend for {ep}: {e}")
