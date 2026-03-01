import os

DEV_PUBLIC  = r'E:\OrderSync - Dev\frontend\public'
PROD_PUBLIC = r'E:\OrderSync\frontend\public'

EXTENSIONS = {'.html', '.js', '.css', '.json'}

print("=== COMPARING DEV vs PROD FILES: Size differences ===\n")

different = []
missing   = []

for root, dirs, files in os.walk(DEV_PUBLIC):
    dirs[:] = [d for d in dirs if d != 'node_modules']
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in EXTENSIONS:
            continue
        rel = os.path.relpath(os.path.join(root, fname), DEV_PUBLIC)
        dev_path  = os.path.join(root, fname)
        prod_path = os.path.join(PROD_PUBLIC, rel)
        if not os.path.exists(prod_path):
            print(f'[MISSING in PROD] {rel}')
            missing.append(rel)
            continue
        dev_size  = os.path.getsize(dev_path)
        prod_size = os.path.getsize(prod_path)

        # Read both files
        with open(dev_path, 'rb') as f:
            dev_bytes = f.read()
        with open(prod_path, 'rb') as f:
            prod_bytes = f.read()

        # Check PROD encoding
        prod_enc = 'OK'
        if prod_bytes[:2] == b'\xff\xfe':
            prod_enc = 'UTF16LE'
        elif prod_bytes[:2] == b'\xfe\xff':
            prod_enc = 'UTF16BE'
        elif prod_bytes[:3] == b'\xef\xbb\xbf':
            prod_enc = 'UTF8BOM'
        else:
            try:
                prod_bytes.decode('utf-8')
            except:
                prod_enc = 'INVALID'

        if prod_enc != 'OK' or dev_bytes != prod_bytes:
            print(f'[DIFF] {rel}  DEV={dev_size}b  PROD={prod_size}b  PROD_ENC={prod_enc}')
            different.append(rel)

print(f'\nDifferent: {len(different)}  Missing: {len(missing)}')

# Also check login.html and gerenciar_tabelas.html specifically
important = [
    r'login\login.html',
    r'login\login.js',
    r'gerenciar_tabelas\gerenciar_tabelas.html',
    r'gerenciar_tabelas\gerenciar_tabelas.js',
]
print('\n=== KEY FILES ENCODING CHECK ===')
for rel in important:
    p = os.path.join(PROD_PUBLIC, rel)
    if os.path.exists(p):
        with open(p, 'rb') as f:
            b = f.read()
        if b[:2] == b'\xff\xfe': enc = 'UTF16LE'
        elif b[:3] == b'\xef\xbb\xbf': enc = 'UTF8BOM'
        else:
            try: b.decode('utf-8'); enc = 'UTF8_OK'
            except: enc = 'INVALID'
        print(f'  {rel}: {enc} ({len(b)} bytes) first8={b[:8].hex()}')
    else:
        print(f'  {rel}: NOT FOUND')
