import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    cur.execute('''
        SELECT t.id_tabela, t.codigo_cliente, t.cliente, c.cadastro_nome_cliente, t.criado_em
        FROM tb_tabela_preco t
        JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = t.codigo_cliente
        WHERE t.codigo_cliente = '125423'
        AND LOWER(TRIM(t.cliente)) != LOWER(TRIM(c.cadastro_nome_cliente))
        ORDER BY t.criado_em DESC
    ''')
    rows = cur.fetchall()
    print(f'Total de divergências com o código 125423: {len(rows)}\n')
    for r in rows:
        print(f'Tabela: {r[0]} | Criada em: {r[4]}')
        print(f'  Digitado: {r[2]}')
        print(f'  Razão:    {r[3]}\n')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
