import os

# Fix ALL directories - both PROD and DEV
DIRS_TO_FIX = [
    r'E:\OrderSync\frontend\public',
    r'E:\OrderSync\frontend',
    r'E:\OrderSync - Dev\frontend\public',
    r'E:\OrderSync - Dev\frontend',
]
SINGLE_FILES = [
    r'E:\OrderSync\frontend\index.html',
    r'E:\OrderSync - Dev\frontend\index.html',
]
EXTENSIONS = {'.html', '.js', '.css', '.json'}
FIXED = []

def try_fix_utf16le_nobom(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    if not raw:
        return 'EMPTY'
    # Already handled BOM cases
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff') or raw[:3] == b'\xef\xbb\xbf':
        return 'HAS_BOM'
    try:
        text_utf8 = raw.decode('utf-8')
    except:
        return 'NOT_UTF8'
    # Signature: starts with Chinese chars that represent <!DOCTYPE or // or window. in UTF-16LE
    if not (text_utf8.startswith('ℼ佄') or text_utf8.startswith('嫠') or
            text_utf8.startswith('慯椠') or text_utf8.startswith('⼯')):
        return 'OK'
    # Reconstruct: each unicode codepoint -> 2 bytes (LE) -> that's the real UTF-8 data
    utf16le_bytes = b''.join(ord(c).to_bytes(2, 'little') for c in text_utf8)
    try:
        real_content = utf16le_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            real_content = utf16le_bytes.decode('latin-1')
        except:
            return 'DECODE_FAIL'
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(real_content)
    return f'FIXED -> starts with: {repr(real_content[:40])}'

for base_dir in DIRS_TO_FIX:
    if not os.path.isdir(base_dir):
        continue
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__', 'dist', 'Backup')]
        if base_dir.endswith('frontend') and root != base_dir:
            # Only process root level files (index.html etc)
            continue
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in EXTENSIONS:
                continue
            fp = os.path.join(root, fname)
            result = try_fix_utf16le_nobom(fp)
            if 'FIXED' in result:
                print(f'[FIXED] {fp}')
                print(f'  {result}')
                FIXED.append(fp)

print(f'\nTotal fixed: {len(FIXED)}')

# Verify key files
for check in [
    r'E:\OrderSync\frontend\public\gerenciar_tabelas\gerenciar_tabelas.html',
    r'E:\OrderSync\frontend\public\login\login.html',
    r'E:\OrderSync\frontend\public\tabela_preco\criacao_tabela_preco.html',
]:
    if os.path.exists(check):
        with open(check, 'rb') as f:
            b = f.read()
        try:
            text = b.decode('utf-8')
            ok = 'OK: ' + repr(text[:40])
        except:
            ok = 'STILL BROKEN'
        print(f'\n{os.path.basename(check)}: {ok}')
