import os

# These files are stored as garbled UTF-8 (actually UTF-16LE bytes misread).
# The pattern: the file starts with chinese chars that decode to HTML when read as UTF-16LE.
# Strategy: re-encode problematic files by:
# 1. Read as bytes
# 2. Interpret as UTF-16LE (swap pairs)
# 3. Write back as UTF-8

PROD_PUBLIC = r'E:\OrderSync\frontend\public'
EXTENSIONS  = {'.html', '.js', '.css', '.json'}

# Heuristic: UTF-16LE without BOM files will have null bytes every 2nd byte
# because ASCII chars in UTF-16LE are: e.g. '<' = 3C 00, '!' = 21 00
# But our file has e2 84 bc e4 bd 84 ... which is VALID multi-byte UTF-8 for Chinese chars.
# This means the content was ALREADY written as UTF-8 Chinese chars (not raw UTF-16 bytes).
# 
# Looking at 'ℼ佄呃偙⁅瑨汭' which is the actual text if we read it as UTF-8:
# ℼ = U+211C, 佄 = U+4F44, 呃 = U+5443, 偙 = U+5059, ⁅ = U+2045, 瑨 = U+7468, 汭 = U+6C6D
# 
# Now: U+211C in UTF-16LE = 1C 21 ... but we need '<!DOCTYPE'
# '<' = U+003C, '!' = U+0021, 'D' = U+0044, 'O' = U+004F, 'C' = U+0043...
# 
# Actually this IS a classic case where the file was encoded in WINDOWS-1252 or similar
# and read back wrong. Let me try a different approach:
# 
# The char sequence ℼ佄呃偙⁅瑨汭 as codepoints:
# 0x211C 0x4F44 0x5443 0x5059 0x2045 0x7468 0x6C6D
# 
# As UTF-16 little-endian PAIRS (reading 2 bytes as one char):
# 1C21 444F 4354 5950 4520 6874 6D6C
# = !< DO CT YP E  ht ml
# Reversed each pair: 3C21 4F44 4354 5950 2045 6874 6D6C
# = <! OD CT PY E  ht ml  -- hmm not quite
# 
# Wait - 0x211C as 2 bytes LE = 1C 21. If we swap -> 21 1C? No.
# 
# Actually: 0x211C in memory (LE) = bytes: 1C 21
# But '<' = 0x003C in UTF-16LE = bytes: 3C 00
# 
# So the file doesn't directly swap to HTML. Let me try yet another approach:
# treat the file bytes as if they are LATIN-1/cp1252 encoding and re-encode as utf-8

FIXED = []

def try_fix_as_latin1(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    # Skip files with BOM already
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff') or raw[:3] == b'\xef\xbb\xbf':
        return 'SKIP_HAS_BOM'
    # Check if first char suggests corruption (Chinese codepoints for what should be '<!')
    try:
        text_utf8 = raw.decode('utf-8')
    except:
        return 'NOT_UTF8'
    
    # If starts with ℼ佄 that's the corruption signature
    if text_utf8.startswith('ℼ佄') or text_utf8.startswith('\ufeffℼ'):
        # This file is UTF-16LE stored without BOM
        # The bytes are correct UTF-16LE bytes, just read as UTF-8 unicode chars
        # We need to get the original UTF-16LE bytes back
        # Strategy: encode back to latin-1 then decode as UTF-16LE? No...
        # 
        # The file on disk: e284bc e4bd84 e59183 ...
        # These are UTF-8 sequences for: ℼ 佄 呃 ...
        # ℼ = U+211C, encoded in UTF-16LE = 1C 21
        # 佄 = U+4F44, encoded in UTF-16LE = 44 4F  
        # 呃 = U+5443, encoded in UTF-16LE = 43 54
        # 偙 = U+5059, encoded in UTF-16LE = 59 50
        # ⁅ = U+2045, encoded in UTF-16LE = 45 20
        # 瑨 = U+7468, encoded in UTF-16LE = 68 74
        # 汭 = U+6C6D, encoded in UTF-16LE = 6D 6C
        # Reading these bytes as ASCII: 1C 21 44 4F 43 54 59 50 45 20 68 74 6D 6C
        # = \x1c ! D O C T Y P E   h t m l  -- YES! That's '<!DOCTYPE html'!
        # 
        # So: take each unicode codepoint, get its UTF-16LE bytes, concatenate -> real content bytes
        utf16le_bytes = b''.join(ord(c).to_bytes(2, 'little') for c in text_utf8)
        # Now decode those bytes as UTF-8 (the actual content)
        try:
            real_content = utf16le_bytes.decode('utf-8')
        except:
            # Try as latin-1 if utf-8 fails
            real_content = utf16le_bytes.decode('latin-1')
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(real_content)
        return f'FIXED (first50: {repr(real_content[:50])})'
    return 'OK'

print("Scanning and fixing...\n")
for root, dirs, files in os.walk(PROD_PUBLIC):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__')]
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in EXTENSIONS:
            continue
        fp = os.path.join(root, fname)
        result = try_fix_as_latin1(fp)
        if 'FIXED' in result:
            print(f'[FIXED] {fp}')
            print(f'  {result}')
            FIXED.append(fp)

# Also fix frontend/index.html
for extra in [r'E:\OrderSync\frontend\index.html']:
    result = try_fix_as_latin1(extra)
    if 'FIXED' in result:
        print(f'[FIXED] {extra}')
        print(f'  {result}')
        FIXED.append(extra)

print(f'\nTotal fixed: {len(FIXED)}')
