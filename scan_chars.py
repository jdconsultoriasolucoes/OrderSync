import os
import glob

PROD_DIR = r"E:\OrderSync\frontend\public"
DEV_DIR = r"E:\OrderSync - Dev\frontend\public"

def check_special_chars(directory):
    print(f"\n--- Scanning {directory} ---")
    files = glob.glob(os.path.join(directory, "**", "*.html"), recursive=True)
    files += glob.glob(os.path.join(directory, "**", "*.css"), recursive=True)
    files += glob.glob(os.path.join(directory, "**", "*.js"), recursive=True)
    
    for file in files:
        if "node_modules" in file:
            continue
        try:
            with open(file, 'rb') as f:
                content_bytes = f.read()
            
            # Try to decode as utf-8
            text = content_bytes.decode('utf-8')
            
            # Look for the replacement character () or strange chinese characters 
            bad_chars = []
            if '' in text:
                bad_chars.append("Replacement Char ()")
            
            # Check if there are unusually high distributions of CJK Unified Ideographs 
            # (which means interpreted as UTF-16LE by mistake previously)
            cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            if cjk_count > 10:
                bad_chars.append(f"High CJK count ({cjk_count})")
                
            if bad_chars:
                print(f"[!] {os.path.relpath(file, directory)}: {', '.join(bad_chars)}")
                
        except UnicodeDecodeError as e:
            print(f"[X] {os.path.relpath(file, directory)}: UnicodeDecodeError - Not valid UTF-8. {e}")

check_special_chars(DEV_DIR)
check_special_chars(PROD_DIR)
