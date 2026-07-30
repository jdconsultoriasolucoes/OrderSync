import psycopg2
import os

DEV_URL = "postgresql://jd_user:t6jq47rYatvkaKm5qmfV9suLolgz8shY@dpg-d9k6b8m417fc73e8mkhg-a.oregon-postgres.render.com/ordersync_dev?sslmode=require"

def verify():
    dump_file = r"scratch\prod_dump.sql"
    if os.path.exists(dump_file):
        size_mb = os.path.getsize(dump_file) / (1024 * 1024)
        print(f"Dump File: {dump_file} ({size_mb:.2f} MB)")
    
    print("Conectando ao banco DEV para verificar tabelas...")
    conn = psycopg2.connect(DEV_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' AND table_type='BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"Total de tabelas em DEV: {len(tables)}")
    for t in tables[:15]:
        cur.execute(f"SELECT count(*) FROM public.\"{t}\";")
        cnt = cur.fetchone()[0]
        print(f"  - {t}: {cnt} registros")
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify()
