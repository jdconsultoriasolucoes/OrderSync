import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    orders_to_check = [110305, 110310]

    for pid in orders_to_check:
        print(f'--- Pedido {pid} ---')
        cur.execute('''
            SELECT 
                p.id_pedido,
                p.codigo_cliente,
                p.cliente as pedido_cliente,
                c.cadastro_nome_cliente as razao_social_atual,
                c.cadastro_nome_fantasia as nome_fantasia_atual
            FROM tb_pedidos p
            LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
            WHERE p.id_pedido = %s
        ''', (pid,))
        row = cur.fetchone()
        if row:
            print(f'  Codigo Cliente: {row[1]}')
            print(f'  Cliente (tb_pedidos): {row[2]}')
            print(f'  Razao Social (t_cadastro_cliente_v2): {row[3]}')
            print(f'  Nome Fantasia (t_cadastro_cliente_v2): {row[4]}')
        else:
            print('  Pedido nao encontrado.')
        print('')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
