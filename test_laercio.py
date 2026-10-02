import psycopg2
from pprint import pprint

conn = psycopg2.connect("postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync")
cur = conn.cursor()

nome_antigo = "LAERCIO YOSHIMASSA SUGUIMOTO"
novo_codigo = "26245"

cur.execute("""
    UPDATE tb_pedidos 
    SET codigo_cliente = %s 
    WHERE (codigo_cliente IS NULL OR codigo_cliente = '' OR LOWER(TRIM(codigo_cliente)) IN ('não cadastrado', 'nao cadastrado')) 
      AND (LOWER(TRIM(cliente)) = LOWER(TRIM(%s)) OR LOWER(cliente) LIKE '%% - ' || LOWER(TRIM(%s)))
""", (novo_codigo, nome_antigo, nome_antigo))

print(f"Updated tb_pedidos: {cur.rowcount} rows")

cur.execute("""
    UPDATE tb_tabela_preco 
    SET codigo_cliente = %s 
    WHERE (codigo_cliente IS NULL OR codigo_cliente = '' OR LOWER(TRIM(codigo_cliente)) IN ('não cadastrado', 'nao cadastrado')) 
      AND (LOWER(TRIM(cliente)) = LOWER(TRIM(%s)) OR LOWER(cliente) LIKE '%% - ' || LOWER(TRIM(%s)))
""", (novo_codigo, nome_antigo, nome_antigo))

print(f"Updated tb_tabela_preco: {cur.rowcount} rows")

conn.commit()
