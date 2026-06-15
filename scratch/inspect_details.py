import psycopg2

db_uri = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
conn = psycopg2.connect(db_uri)
cur = conn.cursor()

# Inspecionar pedido_supra e tamanho em tb_pedidos
print("=== Inspeção de tb_pedidos ===")
for p_id in [109996, 110073]:
    cur.execute(
        "SELECT id_pedido, pedido_supra, length(pedido_supra), status, criado_em, atualizado_em, confirmado_em FROM tb_pedidos WHERE id_pedido = %s;",
        (p_id,)
    )
    res = cur.fetchone()
    print(f"ID {p_id}:")
    print(f"  pedido_supra: {repr(res[1])}")
    print(f"  comprimento: {res[2]}")
    print(f"  status: {res[3]}")
    print(f"  criado_em: {res[4]}")
    print(f"  atualizado_em: {res[5]}")
    print(f"  confirmado_em: {res[6]}")

# Ver logs de importação específicos do pedido 2026002900
print("\n=== Logs de Importação para '2026002900' ===")
cur.execute(
    "SELECT id, pedido_supra, status_processamento, importado_em, detalhes_processamento FROM tb_pedidos_importados WHERE pedido_supra LIKE '%2900' ORDER BY importado_em DESC;"
)
for row in cur.fetchall():
    print(row)

# Ver logs de importação específicos do pedido 2026002992
print("\n=== Logs de Importação para '2026002992' ===")
cur.execute(
    "SELECT id, pedido_supra, status_processamento, importado_em, detalhes_processamento FROM tb_pedidos_importados WHERE pedido_supra LIKE '%2992' ORDER BY importado_em DESC;"
)
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
