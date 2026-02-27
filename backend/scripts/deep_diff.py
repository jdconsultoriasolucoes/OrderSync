"""
Deep diff of key files between PROD and DEV - showing full line-by-line changes.
"""
import os
import difflib

PROD_DIR = "E:/OrderSync"
DEV_DIR  = "E:/OrderSync - Dev"

CRITICAL_FILES = [
    "frontend/public/tabela_preco/criacao_tabela_preco.js",
    "frontend/public/tabela_preco/pedido_cliente.js",
    "frontend/public/gerenciar_tabelas/gerenciar_tabelas.js",
    "frontend/public/produto/produto.js",
    "frontend/public/js/config.js",
    "backend/main.py",
]

for f in CRITICAL_FILES:
    prod_path = os.path.join(PROD_DIR, f)
    dev_path  = os.path.join(DEV_DIR, f)

    print("=" * 70)
    print(f"DIFF: {f}")
    print("=" * 70)

    if not os.path.exists(prod_path):
        print("[MISSING IN PROD - NEW IN DEV]"); print(); continue
    if not os.path.exists(dev_path):
        print("[MISSING IN DEV - ONLY IN PROD]"); print(); continue

    with open(prod_path, 'r', encoding='utf-8', errors='ignore') as p, \
         open(dev_path,  'r', encoding='utf-8', errors='ignore') as d:
        p_lines = p.readlines()
        d_lines = d.readlines()

    diff = list(difflib.unified_diff(p_lines, d_lines,
                                     fromfile=f'PROD', tofile=f'DEV', n=3))
    if not diff:
        print("IDENTICAL - no changes")
    else:
        adds    = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
        removes = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
        print(f"[+{adds} lines added in DEV / -{removes} lines removed from Prod]")
        print()
        # Print lines that were REMOVED from Prod (potential loss of hotfixes)
        in_hunk = False
        for line in diff:
            if line.startswith('@@'):
                in_hunk = True
                print(line, end='')
            elif in_hunk:
                print(line, end='')

    print()
print("Done.")
