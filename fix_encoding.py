import os

PROD_PUBLIC = r'E:\OrderSync\frontend\public'
PROD_INDEX  = r'E:\OrderSync\frontend\index.html'
EXTENSIONS  = {'.html', '.js', '.css', '.json'}

def detect_and_fix(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()

    if raw[:2] == b'\xff\xfe':
        text = raw.decode('utf-16-le').lstrip('\ufeff')
        open(filepath, 'w', encoding='utf-8', newline='').write(text)
        return 'FIXED_UTF16LE'

    if raw[:2] == b'\xfe\xff':
        text = raw.decode('utf-16-be').lstrip('\ufeff')
        open(filepath, 'w', encoding='utf-8', newline='').write(text)
        return 'FIXED_UTF16BE'

    if raw[:3] == b'\xef\xbb\xbf':
        text = raw[3:].decode('utf-8')
        open(filepath, 'w', encoding='utf-8', newline='').write(text)
        return 'FIXED_UTF8BOM'

    try:
        raw.decode('utf-8')
        return 'OK'
    except UnicodeDecodeError:
        return 'ERROR'

fixed = []
errors = []

for root, dirs, files in os.walk(PROD_PUBLIC):
    dirs[:] = [d for d in dirs if d != 'node_modules']
    for fname in files:
        if os.path.splitext(fname)[1].lower() in EXTENSIONS:
            fp = os.path.join(root, fname)
            r = detect_and_fix(fp)
            if 'FIXED' in r:
                print(f'[{r}] {fp}')
                fixed.append(fp)
            elif r == 'ERROR':
                print(f'[ERROR] {fp}')
                errors.append(fp)

r = detect_and_fix(PROD_INDEX)
if 'FIXED' in r:
    print(f'[{r}] {PROD_INDEX}')
    fixed.append(PROD_INDEX)

print(f'\nTotal fixed: {len(fixed)}   Errors: {len(errors)}')
