import os

paths_to_check = [
    r"C:\Program Files\PostgreSQL",
    r"C:\Program Files (x86)\PostgreSQL",
    r"C:\PostgreSQL"
]

pg_dump_path = None
for p in paths_to_check:
    if os.path.exists(p):
        for root, dirs, files in os.walk(p):
            if "pg_dump.exe" in files:
                pg_dump_path = os.path.join(root, "pg_dump.exe")
                break

print(f"pg_dump.exe encontrado em: {pg_dump_path}")
