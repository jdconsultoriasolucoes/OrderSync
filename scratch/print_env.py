import os
for k, v in os.environ.items():
    if "db" in k.lower() or "url" in k.lower() or "sql" in k.lower():
        print(f"{k}: {v[:10]}... (len={len(v)})" if len(v) > 10 else f"{k}: {v}")
