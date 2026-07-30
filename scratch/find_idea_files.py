import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

directories = [r"e:\OrderSync"]

print("=== BUSCANDO ARQUIVOS DE DOCUMENTAÇÃO/IDEIAS ===")
for d in directories:
    for root, dirs, files in os.walk(d):
        if any(x in root for x in [".git", "node_modules", "venv", "dist"]):
            continue
        for f in files:
            if f.endswith((".md", ".txt", ".json")) and not f.startswith("package"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        print(f"\n----------------------------------------")
                        print(f"📄 Arquivo: {full_path}")
                        print(f"Tamanho: {len(content)} caracteres")
                        print("Primeiras 5 linhas:")
                        for line in content.splitlines()[:5]:
                            print(f"   {line}")
                except Exception as e:
                    print(f"Erro em {full_path}: {e}")
