import requests

BASE_URL = 'https://ordersync-backend-edjq.onrender.com/api/tabela_preco'

# Since we don't have a token, we can't easily CREATE a table unless it's unprotected.
# Let's just try to hit /listar using the router correctly
res = requests.get(f'{BASE_URL}/listar?page=1&page_size=10')
print("Status listar:", res.status_code)
if res.status_code == 200:
    data = res.json()
    items = data.get("items", [])
    print(f"Found {len(items)} tables in /listar")
    if items:
        tid = items[0]["id"]
        res_t = requests.get(f'{BASE_URL}/{tid}')
        if res_t.status_code == 200:
            td = res_t.json()
            print("Observacao:", td.get("observacao"))
            prods = td.get("produtos", [])
            if prods:
                print("Markup:", prods[0].get("markup"))
                print("Manual:", prods[0].get("manual_freight"))
                print("Frete Val:", prods[0].get("valor_frete_aplicado"))
        else:
            print(f"Failed to fetch {tid}: {res_t.status_code}")
else:
    print(res.text)
