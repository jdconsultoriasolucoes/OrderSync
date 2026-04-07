import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath("E:/OrderSync/backend/main.py"))

candidates = [
    os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "public")),
    os.path.abspath(os.path.join(BASE_DIR, "frontend", "public")),
]

static_dir = next((p for p in candidates if os.path.isdir(p)), None)

print(f"BASE_DIR: {BASE_DIR}")
print(f"Candidates: {candidates}")
print(f"Detected static_dir: {static_dir}")

if static_dir:
    clientes_path = os.path.join(static_dir, "clientes")
    print(f"Clientes path exists: {os.path.isdir(clientes_path)}")
    if os.path.isdir(clientes_path):
        cliente_html = os.path.join(clientes_path, "cliente.html")
        print(f"cliente.html exists: {os.path.isfile(cliente_html)}")
        if os.path.isfile(cliente_html):
             with open(cliente_html, 'r', encoding='utf-8') as f:
                 content = f.read()
                 print(f"Found 'valor' in cliente.html: {'valor' in content}")
