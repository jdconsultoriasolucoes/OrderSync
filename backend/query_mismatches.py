import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    cur.execute('''
        SELECT DISTINCT t.id_tabela, t.codigo_cliente, t.cliente AS nome_digitado, c.cadastro_nome_cliente AS razao_social, c.cadastro_nome_fantasia AS nome_fantasia
        FROM tb_tabela_preco t
        JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = t.codigo_cliente
        WHERE LOWER(TRIM(t.cliente)) != LOWER(TRIM(c.cadastro_nome_cliente))
        AND LOWER(TRIM(t.cliente)) != LOWER(TRIM(COALESCE(c.cadastro_nome_fantasia, '')))
        AND t.cliente IS NOT NULL AND TRIM(t.cliente) != ''
        AND t.codigo_cliente != 'Não cadastrado'
    ''')
    rows = cur.fetchall()
    print(f'Total de divergências encontradas: {len(rows)}\n')
    for r in rows[:20]:  # Limit to first 20 to avoid giant output
        print(f'Tabela: {r[0]} | Cod: {r[1]}')
        print(f'  Digitado: {r[2]}')
        print(f'  Razão:    {r[3]}')
        print(f'  Fantasia: {r[4]}\n')
    if len(rows) > 20:
        print('...')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
