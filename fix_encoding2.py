import os, struct

# The sequence e2 84 bc is '<!D' read as UTF-16LE pairs:
# 0x84e2 = ℼ , 0xbde4 ..
# When we swap pairs in UTF-16LE: 0x3C21 = '<!' , 0x444F = 'DO'
# So we detect UTF-16LE-no-BOM by checking if swapping byte pairs gives valid ASCII/UTF-8 start

DIRS = [
    r'E:\OrderSync\frontend\public',
    r'E:\OrderSync\frontend',  # for index.html
]
EXTENSIONS = {'.html', '.js', '.css', '.json'}

def is_utf16le_no_bom(raw):
    """Check if content is UTF-16LE without BOM by trying to decode"""
    if len(raw) < 4 or len(raw) % 2 != 0:
        return False
    # Try decode as utf-16-le
    try:
        text = raw.decode('utf-16-le')
        # If it decodes and starts with recognizable HTML/JS/CSS chars, it's UTF-16LE
        stripped = text.lstrip('\ufeff')
        if stripped.startswith('<!') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('window') or stripped.startswith('{') or stripped.startswith('\r\n') or stripped.startswith('\n'):
            # Also verify the original can't be valid UTF-8 with these bytes
            try:
                raw.decode('utf-8')
                return False  # it's valid UTF-8, don't touch it
            except UnicodeDecodeError:
                return True  # invalid UTF-8, must be UTF-16LE
        return False
    except:
        return False

fixed = []
skipped = []

for base_dir in DIRS:
    if base_dir.endswith('frontend'):
        # Only process index.html in the root frontend dir
        fp = os.path.join(base_dir, 'index.html')
        if os.path.exists(fp):
            with open(fp, 'rb') as f:
                raw = f.read()
            # Check for any BOM
            if raw[:2] == b'\xff\xfe':
                text = raw.decode('utf-16-le').lstrip('\ufeff')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF16LE_BOM] {fp}')
                fixed.append(fp)
            elif raw[:2] == b'\xfe\xff':
                text = raw.decode('utf-16-be').lstrip('\ufeff')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF16BE_BOM] {fp}')
                fixed.append(fp)
            elif raw[:3] == b'\xef\xbb\xbf':
                text = raw[3:].decode('utf-8')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF8BOM] {fp}')
                fixed.append(fp)
            elif is_utf16le_no_bom(raw):
                text = raw.decode('utf-16-le').lstrip('\ufeff')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF16LE_NOBOM] {fp}')
                fixed.append(fp)
        continue

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__')]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in EXTENSIONS:
                continue
            fp = os.path.join(root, fname)
            with open(fp, 'rb') as f:
                raw = f.read()

            if raw[:2] == b'\xff\xfe':
                text = raw.decode('utf-16-le').lstrip('\ufeff')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF16LE_BOM] {fp}')
                fixed.append(fp)
            elif raw[:2] == b'\xfe\xff':
                text = raw.decode('utf-16-be').lstrip('\ufeff')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF16BE_BOM] {fp}')
                fixed.append(fp)
            elif raw[:3] == b'\xef\xbb\xbf':
                text = raw[3:].decode('utf-8')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF8BOM] {fp}')
                fixed.append(fp)
            elif is_utf16le_no_bom(raw):
                text = raw.decode('utf-16-le').lstrip('\ufeff')
                open(fp, 'w', encoding='utf-8', newline='').write(text)
                print(f'[FIXED_UTF16LE_NOBOM] {fp}')
                fixed.append(fp)

print(f'\nTotal fixed: {len(fixed)}')

# Verify gerenciar_tabelas.html
gt = r'E:\OrderSync\frontend\public\gerenciar_tabelas\gerenciar_tabelas.html'
with open(gt, 'rb') as f:
    b = f.read()
print(f'\nVerify gerenciar_tabelas.html: first bytes hex={b[:8].hex()} content={repr(b[:30].decode("utf-8","replace"))}')
