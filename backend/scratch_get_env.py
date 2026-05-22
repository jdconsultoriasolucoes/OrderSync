import os
import glob

print("Current files matching .env*:")
for f in glob.glob(".env*") + glob.glob("../.env*"):
    print(f"File: {f}")
    try:
        with open(f, "r", encoding="utf-8") as file:
            print(file.read()[:500])
    except Exception as e:
        print(f"Error reading {f}: {e}")
