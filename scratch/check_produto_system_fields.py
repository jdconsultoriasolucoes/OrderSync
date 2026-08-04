import re

# 1. Read produto.html
with open(r'e:\OrderSync\frontend\public\produto\produto.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

inputs = re.findall(r'<(?:input|select|textarea)[^>]*?(?:id|name)=["\']([^"\']+)["\'][^>]*>', html, re.IGNORECASE)
labels = re.findall(r'<label[^>]*>(.*?)</label>', html, re.IGNORECASE | re.DOTALL)
labels_clean = [re.sub(r'<.*?>', '', l).strip() for l in labels if re.sub(r'<.*?>', '', l).strip()]

print("=== PRODUTO.HTML INPUTS ===")
for i in sorted(list(set(inputs))):
    print(" -", i)

print("\n=== PRODUTO.HTML LABELS ===")
for l in labels_clean:
    print(" -", l)

# 2. Check SQL schema for t_cadastro_produto in migration_dev_to_prod.sql
with open(r'e:\OrderSync\migration_dev_to_prod.sql', 'r', encoding='utf-8', errors='ignore') as f:
    sql = f.read()

tables = re.findall(r'CREATE TABLE [^;]+;', sql, re.IGNORECASE)
for t in tables:
    if 't_cadastro_produto' in t or 't_produto' in t:
        print("\n=== SQL PRODUTO TABLE DEFINITION ===")
        print(t)
