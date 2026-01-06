import os
import re
from collections import defaultdict

def scan_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    defs = defaultdict(list)
    # Python pattern: def name(...)
    # JS pattern: function name(...) or async function name(...)
    # We ignore anonymous functions like "const x = () =>" for now as they are harder to dup-detect by name
    
    if filepath.endswith('.py'):
        pattern = re.compile(r'^\s*def\s+([a-zA-Z0-9_]+)\s*\(')
    elif filepath.endswith('.js'):
        pattern = re.compile(r'^\s*(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(')
    else:
        return

    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            name = match.group(1)
            defs[name].append(i + 1)

    dups = {k: v for k, v in defs.items() if len(v) > 1}
    if dups:
        print(f"\n[DUPLICATES FOUND] {filepath}")
        for name, lines in dups.items():
            print(f"  - {name}: lines {lines}")

def scan_directory(root_path):
    for root, dirs, files in os.walk(root_path):
        if 'node_modules' in root or '__pycache__' in root or '.git' in root or 'venv' in root:
            continue
        for file in files:
            if file.endswith('.py') or file.endswith('.js'):
                scan_file(os.path.join(root, file))

if __name__ == "__main__":
    scan_directory("e:\\OrderSync\\backend")
    scan_directory("e:\\OrderSync\\frontend\\public")
