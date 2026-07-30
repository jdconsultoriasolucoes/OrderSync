import subprocess
import os
import sys

PROD_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"
DEV_URL = "postgresql://jd_user:t6jq47rYatvkaKm5qmfV9suLolgz8shY@dpg-d9k6b8m417fc73e8mkhg-a.oregon-postgres.render.com/ordersync_dev?sslmode=require"

PG_DUMP = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
PSQL = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"
DUMP_FILE = os.path.abspath(r"scratch\prod_dump.sql")

def run():
    print(f"1. Iniciando pg_dump do banco PROD para '{DUMP_FILE}'...")
    dump_cmd = [
        PG_DUMP,
        f"--dbname={PROD_URL}",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        f"--file={DUMP_FILE}"
    ]
    res_dump = subprocess.run(dump_cmd, capture_output=True, text=True)
    if res_dump.returncode != 0:
        print(f"ERRO NO PG_DUMP: {res_dump.stderr}")
        sys.exit(1)
    
    file_size_mb = os.path.getsize(DUMP_FILE) / (1024 * 1024)
    print(f"SUCCESS! Dump criado com sucesso. Tamanho: {file_size_mb:.2f} MB")

    print(f"\n2. Restaurando dump no banco DEV...")
    restore_cmd = [
        PSQL,
        f"--dbname={DEV_URL}",
        f"--file={DUMP_FILE}"
    ]
    res_restore = subprocess.run(restore_cmd, capture_output=True, text=True)
    print(f"SUCCESS! Restauração em DEV finalizada.")
    print("Log parcial de restauração:")
    lines = res_restore.stdout.splitlines()
    for l in lines[-10:]:
        print(f"  {l}")

if __name__ == "__main__":
    run()
