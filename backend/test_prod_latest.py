import requests

# Try finding a valid table
tables = []
try:
    res = requests.get('https://ordersync-backend-edjq.onrender.com/api/tabela_preco?page=1&page_size=20')
    if res.status_code == 200:
        data = res.json()
        if isinstance(data, dict) and "items" in data:
            tables = data["items"]
        elif isinstance(data, list):
            tables = data
except Exception as e:
    print(e)

print(f"Found {len(tables)} tables.")
for t in tables[:3]:
    tid = t.get("id") or t.get("id_tabela")
    if tid:
        print(f"\nFetching Table {tid}...")
        res_t = requests.get(f'https://ordersync-backend-edjq.onrender.com/api/tabela_preco/{tid}')
        if res_t.status_code == 200:
            td = res_t.json()
            print(f"Observacao: {td.get('observacao')}")
            prods = td.get("produtos", [])
            if prods:
                p = prods[0]
                print(f"Markup: {p.get('markup')}")
                print(f"Manual Freight: {p.get('manual_freight')}")
                print(f"Valor Frete Aplicado: {p.get('valor_frete_aplicado')}")
            else:
                print("No products")
