"""
Fix encoding corruption caused by PowerShell Set-Content
which wrote files as UTF-16LE instead of UTF-8.

This script:
1. Reads each JS/HTML/JSON file in the Dev frontend
2. Fixes any encoding issues 
3. Rewrites with explicit UTF-8 BOM-less encoding
4. Also ensures the URL replacement is correct
"""
import os

root = "E:/OrderSync - Dev/frontend/public"
OLD_URL = "ordersync-backend-59d2.onrender.com"
NEW_URL = "ordersync-backend-edjq.onrender.com"

extensions = ('.js', '.html', '.json', '.css')

fixed = 0
errors = 0

for dirpath, dirnames, filenames in os.walk(root):
    for filename in filenames:
        if not filename.endswith(extensions):
            continue
        filepath = os.path.join(dirpath, filename)
        
        # Try reading as UTF-8 first, then fall back to latin-1
        content = None
        for enc in ('utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'latin-1', 'cp1252'):
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except Exception:
                continue
        
        if content is None:
            print(f"ERROR: Cannot read {filepath}")
            errors += 1
            continue
        
        # Apply URL replacement if needed
        new_content = content.replace(OLD_URL, NEW_URL)
        
        # Always rewrite as clean UTF-8 (no BOM)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            if new_content != content:
                print(f"FIXED+URL: {filepath}")
            else:
                print(f"FIXED ENC: {filepath}")
            fixed += 1
        except Exception as e:
            print(f"ERROR writing {filepath}: {e}")
            errors += 1

print(f"\nDone. {fixed} files fixed, {errors} errors.")
