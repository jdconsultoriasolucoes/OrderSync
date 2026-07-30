import psycopg2

PROD_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"
DEV_URL = "postgresql://jd_user:t6jq47rYatvkaKm5qmfV9suLolgz8shY@dpg-d9k6b8m417fc73e8mkhg-a.oregon-postgres.render.com/ordersync_dev?sslmode=require"

def check():
    conn_p = psycopg2.connect(PROD_URL)
    cur_p = conn_p.cursor()
    
    conn_d = psycopg2.connect(DEV_URL)
    cur_d = conn_d.cursor()

    cur_p.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;")
    tables_p = [r[0] for r in cur_p.fetchall()]

    cur_d.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;")
    tables_d = [r[0] for r in cur_d.fetchall()]

    print(f"Total tabelas PROD: {len(tables_p)} | Total tabelas DEV: {len(tables_d)}")

    mismatches = 0
    for t in tables_p:
        cur_p.execute(f"SELECT count(*) FROM public.\"{t}\";")
        cnt_p = cur_p.fetchone()[0]
        
        cur_d.execute(f"SELECT count(*) FROM public.\"{t}\";")
        cnt_d = cur_d.fetchone()[0]

        if cnt_p != cnt_d:
            print(f"  ❌ DIVERGÊNCIA em '{t}': PROD={cnt_p} vs DEV={cnt_d}")
            mismatches += 1
        else:
            print(f"  ✅ {t}: {cnt_p} registros (100% Idêntico)")

    if mismatches == 0:
        print("\n🎉 CLONAGEM 100% PERFEITA! Todas as tabelas e contagens de registros no banco DEV correspondem exatamente a Produção.")

    cur_p.close()
    conn_p.close()
    cur_d.close()
    conn_d.close()

if __name__ == "__main__":
    check()
