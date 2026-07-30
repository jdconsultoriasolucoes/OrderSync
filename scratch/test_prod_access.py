import psycopg2

PROD_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    print("Conectando ao banco PROD...")
    conn = psycopg2.connect(PROD_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' AND table_type='BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"SUCESSO CONECTADO AO PROD! Total de tabelas: {len(tables)}")
    print("Tabelas encontradas:")
    for t in tables:
        cur.execute(f"SELECT count(*) FROM public.\"{t}\";")
        cnt = cur.fetchone()[0]
        print(f"  - {t}: {cnt} registros")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Erro de conexão PROD: {e}")
