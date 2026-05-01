import requests
res = requests.get('https://ordersync-backend-edjq.onrender.com/api/tabela_preco/')
if res.status_code == 200:
    data = res.json()
    if data.get("items"):
        first_id = data["items"][0]["id"]
        res_t = requests.get(f'https://ordersync-backend-edjq.onrender.com/api/tabela_preco/{first_id}')
        print(f"Table {first_id}:")
        t_data = res_t.json()
        print("Observacao:", t_data.get("observacao"))
        print("Manual Freight:", t_data["produtos"][0].get("manual_freight"))
    else:
        print("No tables.")
else:
    print("Error:", res.status_code)
