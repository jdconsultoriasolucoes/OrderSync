import psycopg2

DEV_URL = "postgresql://jd_user:t6jq47rYatvkaKm5qmfV9suLolgz8shY@dpg-d9k6b8m417fc73e8mkhg-a.oregon-postgres.render.com/ordersync_dev?sslmode=require"

conn = psycopg2.connect(DEV_URL)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
count_tables = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM tb_pedidos;")
cnt_pedidos = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM tb_pedidos_itens;")
cnt_itens = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM t_cadastro_cliente_v2;")
cnt_cli = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM tb_tabela_preco;")
cnt_tp = cur.fetchone()[0]

print(f"DEV DB OK! Total Tabelas: {count_tables}")
print(f"  - tb_pedidos: {cnt_pedidos} registros")
print(f"  - tb_pedidos_itens: {cnt_itens} registros")
print(f"  - t_cadastro_cliente_v2: {cnt_cli} registros")
print(f"  - tb_tabela_preco: {cnt_tp} registros")

cur.close()
conn.close()
