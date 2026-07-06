with open(r'e:\OrderSync\frontend\public\produto\produto.js', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(r"\'", "'")
with open(r'e:\OrderSync\frontend\public\produto\produto.js', 'w', encoding='utf-8') as f:
    f.write(content)
