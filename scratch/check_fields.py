import re

with open(r'e:\OrderSync\frontend\public\clientes\cliente.html', 'r', encoding='utf-8', errors='ignore') as f:
    html_content = f.read()

inputs = re.findall(r'<(?:input|select|textarea)[^>]*?(?:id|name)=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
labels = re.findall(r'<label[^>]*>(.*?)</label>', html_content, re.IGNORECASE | re.DOTALL)
labels_clean = [re.sub(r'<.*?>', '', l).strip() for l in labels if re.sub(r'<.*?>', '', l).strip()]

print('=== CLIENTE.HTML INPUT/SELECT/TEXTAREA IDs/NAMEs ===')
for i in sorted(list(set(inputs))):
    print(' -', i)

print('\n=== CLIENTE.HTML LABELS ===')
for l in labels_clean:
    print(' -', l)
