import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from routers.tabela_preco import obter_tabela

res = obter_tabela(1)
print("Result of obter_tabela(1):")
print("nome_tabela:", res.get("nome_tabela"))
print("nome_arquivo_estoque:", res.get("nome_arquivo_estoque"))
print("Produtos e estoques:")
for p in res.get("produtos", []):
    print(f"  Prod: {p['codigo_produto_supra']}, Status: {p['status_atual']}, Disp: {p['estoque_disponivel']}, Fut: {p['estoque_futuro']}")
