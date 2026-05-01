import requests

# Try finding a valid table
for i in range(10, 0, -1):
    res = requests.get(f'https://ordersync-backend-edjq.onrender.com/api/tabela_preco/{i}')
    if res.status_code == 200:
        data = res.json()
        print(f"Table {i} found!")
        print("Keys in response:", data.keys())
        if "observacao" in data:
            print("Backend IS returning observacao!")
        else:
            print("Backend IS NOT returning observacao!")
        break
