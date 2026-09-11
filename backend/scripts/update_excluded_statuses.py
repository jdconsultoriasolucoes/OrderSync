import psycopg2

conn=psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require')
cur=conn.cursor()

# Retrieve the exact string from DB to avoid encoding issues
cur.execute("SELECT status FROM tb_pedidos WHERE status != 'FATURADO_SUPRA' LIMIT 1;")
res = cur.fetchone()
orcamento_status = res[0] if res else 'Orçamento'

excluded_ids_raw = [
    "2.026.004.421", "2.026.004.364", "2.026.004.371", "2.026.004.325",
    "2.026.004.281", "2.026.004.429", "2.026.004.427", "2.026.004.394",
    "2.026.004.393", "2.026.004.339", "2.026.004.430", "2.026.004.419",
    "2.026.004.409", "2.026.004.366", "2.026.004.158", "2.026.004.420",
    "2.026.004.415", "2.026.004.323", "2.026.004.333", "2.026.004.173",
    "2.026.004.396", "2.026.004.368", "2.026.004.412", "2.026.004.389",
    "2.026.004.431", "2.026.004.414", "2.026.004.428", "2.026.004.426",
    "2.026.004.413", "2.026.004.235", "2.026.004.424", "2.026.004.360",
    "2.026.004.272", "2.026.004.263", "2.026.004.262", "2.026.004.261",
    "2.026.004.335"
]

excluded_ids = [x.replace(".", "") for x in excluded_ids_raw]

cur.execute("UPDATE tb_pedidos SET status = %s WHERE pedido_supra = ANY(%s);", (orcamento_status, excluded_ids))
updated_count = cur.rowcount
conn.commit()

print(f"Updated {updated_count} orders to {repr(orcamento_status)}")

cur.close()
conn.close()
