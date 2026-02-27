import requests

def test_api():
    try:
        # Pega a listagem (POST exige JSON body)
        res_list = requests.post("https://ordersync-backend-edjq.onrender.com/api/pedido/listagem?limit=1", json={})
        if res_list.status_code == 200:
            data = res_list.json()
            if data.get("data"):
                pid = data["data"][0]["numero_pedido"]
                print(f"Buscando resumo do pedido {pid}...")
                
                # Pega o resumo
                res_resumo = requests.get(f"https://ordersync-backend-edjq.onrender.com/api/pedido/{pid}/resumo")
                if res_resumo.status_code == 200:
                    resumo = res_resumo.json()
                    print(f"SUCESSO! peso_liquido_calculado = {resumo.get('peso_liquido_calculado')}")
                else:
                    print(f"Erro no resumo: {res_resumo.status_code} - {res_resumo.text}")
            else:
                print("Listagem vazia.")
        else:
             print(f"Erro na listagem: {res_list.status_code} - {res_list.text}")
    except Exception as e:
        print("Erro de rede:", e)

if __name__ == "__main__":
    test_api()
