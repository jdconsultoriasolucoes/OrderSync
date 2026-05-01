import requests
import json

res = requests.get('https://ordersync-backend-edjq.onrender.com/api/tabela_preco/4')
if res.status_code == 200:
    data = res.json()
    print("Observacao:", data.get("observacao"))
    if data.get("produtos"):
        p = data["produtos"][0]
        print("Manual Freight:", p.get("manual_freight"))
        print("Valor Frete:", p.get("valor_frete_aplicado"))
        print("Markup:", p.get("markup"))
    else:
        print("No produtos")
else:
    print("Error:", res.status_code)
