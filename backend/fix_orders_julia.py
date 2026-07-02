import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    print('--- Atualizando tb_pedidos ---')
    cur.execute('''UPDATE tb_pedidos SET cliente = 'JULIA PACHECO RODRIGUES' WHERE id_pedido IN (110305, 110310);''')
    print(f'Linhas atualizadas em tb_pedidos: {cur.rowcount}')

    print('--- Atualizando tb_tabela_preco ---')
    cur.execute('''UPDATE tb_tabela_preco SET cliente = 'JULIA PACHECO RODRIGUES' WHERE id_tabela IN (700, 304);''')
    print(f'Linhas atualizadas em tb_tabela_preco: {cur.rowcount}')

    conn.commit()
    conn.close()
    print('Atualização concluída com sucesso!')
except Exception as e:
    print(f'Erro ao conectar ou atualizar: {e}')
