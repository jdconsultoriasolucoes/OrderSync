"""
Compares all relevant files between PROD (E:/OrderSync) and DEV (E:/OrderSync - Dev).
Also checks git log of Prod for hotfixes made after Feb 12, 2026.
"""
import os
import difflib
import subprocess

PROD_DIR = "E:/OrderSync"
DEV_DIR = "E:/OrderSync - Dev"

# --- Git log in PROD to find recent hotfixes ---
print("=" * 60)
print("RECENT COMMITS IN PROD (since Feb 12, 2026)")
print("=" * 60)
try:
    result = subprocess.check_output(
        ['git', 'log', '--since=2026-02-12', '--name-only', '--pretty=format:COMMIT|%h|%ad|%s'],
        cwd=PROD_DIR, text=True, stderr=subprocess.DEVNULL
    )
    print(result)
except Exception as e:
    print(f"Error reading Prod git log: {e}")

print()

# --- File-by-file diff ---
# Files to compare between Prod and Dev
files_to_check = [
    # Backend
    "backend/models/cliente_v2.py",
    "backend/schemas/cliente.py",
    "backend/schemas/pedidos.py",
    "backend/services/cliente.py",
    "backend/services/pedidos.py",
    "backend/services/pedido_confirmacao_service.py",
    "backend/services/pedido_pdf_data.py",
    "backend/services/pdf_service.py",
    "backend/routers/pedidos.py",
    "backend/routers/pedido_pdf.py",
    "backend/main.py",
    # Frontend
    "frontend/public/pedido/pedido.js",
    "frontend/public/clientes/cliente.html",
    "frontend/public/tabela_preco/tabela_preco.html",
    "frontend/public/tabela_preco/tabela_preco.js",
    "frontend/public/tabela_preco/listar_tabelas.js",
    "frontend/public/tabela_preco/criacao_tabela_preco.js",
    "frontend/public/tabela_preco/pedido_cliente.js",
    "frontend/public/produto/produto.js",
    "frontend/public/gerenciar_tabelas/gerenciar_tabelas.js",
    "frontend/public/js/config.js",
]

print("=" * 60)
print("FILE DIFF SUMMARY: PROD vs DEV")
print("=" * 60)

for f in files_to_check:
    prod_path = os.path.join(PROD_DIR, f)
    dev_path  = os.path.join(DEV_DIR, f)

    if not os.path.exists(prod_path) and not os.path.exists(dev_path):
        print(f"[BOTH MISSING]  {f}")
        continue
    if not os.path.exists(prod_path):
        print(f"[NEW IN DEV]    {f}")
        continue
    if not os.path.exists(dev_path):
        print(f"[MISSING IN DEV]{f}")
        continue

    with open(prod_path, 'r', encoding='utf-8', errors='ignore') as p, \
         open(dev_path,  'r', encoding='utf-8', errors='ignore') as d:
        p_lines = p.readlines()
        d_lines = d.readlines()

    diff = list(difflib.unified_diff(p_lines, d_lines,
                                     fromfile=f'PROD/{f}', tofile=f'DEV/{f}', n=2))
    if diff:
        adds    = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
        removes = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
        print(f"[DIFFERENT]     {f}  (+{adds} / -{removes} lines)")
    else:
        print(f"[IDENTICAL]     {f}")

print()
print("Done.")
