import requests

def check_remote():
    url = "https://ordersync-backend-edjq.onrender.com/api/produto/renovar_validade_global"
    print(f"Checking {url}")
    try:
        # We expect 401 (Unauthorized) if it exists, or 404 if it doesn't.
        # We aren't sending auth token here.
        resp = requests.post(url, json={"nova_validade": "2026-01-01"})
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_remote()
