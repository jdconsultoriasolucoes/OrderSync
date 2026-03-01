import os

DEV_GT = r'E:\OrderSync - Dev\frontend\public\gerenciar_tabelas\gerenciar_tabelas.html'
PROD_GT = r'E:\OrderSync\frontend\public\gerenciar_tabelas\gerenciar_tabelas.html'

for label, path in [('DEV', DEV_GT), ('PROD', PROD_GT)]:
    with open(path, 'rb') as f:
        b = f.read()
    print(f'{label}: {len(b)} bytes')
    print(f'  first 20 bytes hex: {b[:20].hex()}')
    print(f'  first 20 bytes raw: {b[:20]}')
    # Try decode
    if b[:2] == b'\xff\xfe':
        print(f'  Encoding: UTF-16 LE BOM')
        text = b.decode('utf-16-le', errors='replace')[:200]
    elif b[:3] == b'\xef\xbb\xbf':
        print(f'  Encoding: UTF-8 BOM')
        text = b[3:].decode('utf-8', errors='replace')[:200]
    else:
        try:
            text = b.decode('utf-8', errors='replace')[:200]
            print(f'  Encoding: UTF-8 (or latin-1)')
        except:
            text = '???'
    print(f'  Content start: {repr(text[:100])}')
    print()
