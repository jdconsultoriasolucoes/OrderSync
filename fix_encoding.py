import os, sys

PROD_PUBLIC = r'E:\OrderSync\frontend\public'
PROD_INDEX  = r'E:\OrderSync\frontend\index.html'

EXTENSIONS = {'.html', '.js', '.css', '.json'}

def detect_and_fix(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    # Check for UTF-16 LE BOM (FF FE)
    if raw[:2] == b'\xff\xfe':
        text = raw.decode('utf-16-le')
        if text.startswith('\ufeff'):
            text = text[1:]
        # Preserve original line endings style (CRLF for Windows)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        return 'FIXED_UTF16LE'
    
    # Check for UTF-16 BE BOM (FE FF)
    if raw[:2] == b'\xfe\xff':
        text = raw.decode('utf-16-be')
        if text.startswith('\ufeff'):
            text = text[1:]
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        return 'FIXED_UTF16BE'
    
    # Check for UTF-8 BOM (EF BB BF)
    if raw[:3] == b'\xef\xbb\xbf':
        text = raw[3:].decode('utf-8')
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        return 'FIXED_UTF8BOM'
    
    # Try decode as UTF-8 to verify it's valid
    try:
        raw.decode('utf-8')
        return 'OK'
    except UnicodeDecodeError:
        return 'INVALID_ENCODING'

fixed = []
errors = []

# Scan all files in public/
for root, dirs, files in os.walk(PROD_PUBLIC):
    dirs[:] = [d for d in dirs if d != 'node_modules']
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext in EXTENSIONS:
            fp = os.path.join(root, fname)
            result = detect_and_fix(fp)
            if 'FIXED' in result:
                print(f'[{result}] {fp}')
                fixed.append(fp)
            elif result == 'INVALID_ENCODING':
                print(f'[ERROR] {fp}')
                errors.append(fp)

# Also fix index.html
result = detect_and_fix(PROD_INDEX)
if 'FIXED' in result:
    print(f'[{result}] {PROD_INDEX}')
    fixed.append(PROD_INDEX)
elif result == 'INVALID_ENCODING':
    print(f'[ERROR] {PROD_INDEX}')

print(f'\nSummary: {len(fixed)} fixed, {len(errors)} errors')
print('Scanned all .html/.js/.css/.json files in frontend/public/')
if errors:
    print('Files with unrecoverable encoding errors:', errors)
if not fixed:
    print('No UTF-16 files found. All files are already valid UTF-8.')
