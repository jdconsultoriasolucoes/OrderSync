import requests
res = requests.get('https://ordersync-backend-edjq.onrender.com/tabela_preco/criacao_tabela_preco.js')
if res.status_code == 200:
    text = res.text
    if 'valor_frete_aplicado' in text:
        print("YES! File has valor_frete_aplicado")
        if 'mkInput.value = Number(mkVal).toFixed(2);' in text:
            print("YES! File has markup fix")
        else:
            print("NO! File is missing markup fix")
    else:
        print("NO! File is missing valor_frete_aplicado")
else:
    print("Error:", res.status_code)
