import psycopg2

orders = [
    "2026002935",
    "2026002753",
    "2026002938",
    "2026002939",
    "2026002757",
    "2026002746",
    "2026002890",
    "2026002884",
    "2026002859",
    "2026002992",
    "2026002819",
    "2026002900",
    "2026002965",
    "2026002861",
    "2026002955",
    "2026002842",
    "2026002769"
]

db_uri = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

print("Conectando ao banco de dados...")
conn = psycopg2.connect(db_uri)
cur = conn.cursor()

print("\n--- Buscando na tabela tb_pedidos_importados ---")
for order in orders:
    # 1. Busca exata em tb_pedidos_importados
    cur.execute(
        "SELECT id, pedido_supra, status_processamento, importado_em, detalhes_processamento FROM tb_pedidos_importados WHERE pedido_supra = %s;",
        (order,)
    )
    exact_res = cur.fetchall()
    
    # 2. Busca pelo sufixo (ex: '2935') em tb_pedidos_importados
    suffix = order[-4:] if len(order) >= 4 else order
    cur.execute(
        "SELECT id, pedido_supra, status_processamento, importado_em FROM tb_pedidos_importados WHERE pedido_supra LIKE %s;",
        ('%' + suffix,)
    )
    like_res = cur.fetchall()

    # 3. Busca em tb_pedidos
    cur.execute(
        "SELECT id_pedido, pedido_supra, status, total_pedido, criado_em, confirmado_em FROM tb_pedidos WHERE pedido_supra = %s OR pedido_supra LIKE %s;",
        (order, '%' + suffix)
    )
    pedidos_res = cur.fetchall()

    print(f"\nPedido analisado: {order} (Sufixo: {suffix})")
    print(f"  - tb_pedidos_importados (Exato): {exact_res}")
    print(f"  - tb_pedidos_importados (Like %{suffix}): {like_res}")
    print(f"  - tb_pedidos (Exato ou Like %{suffix}): {pedidos_res}")

cur.close()
conn.close()
print("\nConclusão da verificação.")
