"""
Busca o peso unitário de cada produto do pedido 391 via a rota dados_pdf
e mostra os cálculos individuais.
"""
import requests

BACKEND = "https://ordersync-backend-edjq.onrender.com"

# Primeiro pega o resumo do pedido para ter os itens
resp = requests.get(f"{BACKEND}/api/pedido/391/dados_pdf", timeout=60)
data = resp.json()

print("Cálculo detalhado do peso líquido:")
print("=" * 70)

total_calculado = 0.0
for item in data.get("itens", []):
    qtd = item.get("quantidade", 0)
    if qtd == 0:
        continue
    cod = item.get("codigo")
    nome = item.get("produto", "")[:35]
    
    # O modelo PedidoPdfItem não tem campo de peso individual
    # Mas sabemos que o total é 875 com esses 3 itens
    # Verificamos pelo total e as qtds: qual peso unitário cada produto tem?
    print(f"  {cod} | {nome}")
    print(f"    qtd = {qtd}")

print()
print(f"total_peso_liquido do servidor = {data.get('total_peso_liquido')} kg")
print()

# Agora vamos buscar o PDF para ver como ele exibe
print("Buscando estrutura completa dos itens...")
for item in data.get("itens", []):
    qtd = item.get("quantidade", 0)
    if qtd == 0:
        continue
    print(f"\nItem: {item.get('codigo')}")
    for k, v in item.items():
        print(f"  {k}: {v}")
