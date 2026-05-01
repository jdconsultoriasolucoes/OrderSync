import requests
res = requests.get('https://ordersync-backend-edjq.onrender.com/api/tabela_preco/listar') # Or whatever the route is
# Wait, the route is /api/tabela_preco with query params
res = requests.get('https://ordersync-backend-edjq.onrender.com/api/tabela_preco?page=1&page_size=1')
if res.status_code == 200:
    data = res.json()
    if data.get("items"):
        first_id = data["items"][0]["id"]
        print("Found latest table ID:", first_id)
        res_t = requests.get(f'https://ordersync-backend-edjq.onrender.com/api/tabela_preco/{first_id}')
        t_data = res_t.json()
        print("Observacao:", t_data.get("observacao"))
        if t_data.get("produtos"):
            print("Manual Freight:", t_data["produtos"][0].get("manual_freight"))
        else:
            print("No items")
    else:
        print("No tables.")
else:
    print("Error:", res.status_code, res.text)
