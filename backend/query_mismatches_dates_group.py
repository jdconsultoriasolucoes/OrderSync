import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    cur.execute('''
        SELECT TO_CHAR(t.criado_em, 'YYYY-MM') AS mes, COUNT(*) 
        FROM tb_tabela_preco t
        JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = t.codigo_cliente
        WHERE t.codigo_cliente = '125423'
        AND LOWER(TRIM(t.cliente)) != LOWER(TRIM(c.cadastro_nome_cliente))
        GROUP BY mes
        ORDER BY mes DESC
    ''')
    rows = cur.fetchall()
    print('Distribuição por Mês (Apenas para o código 125423):\n')
    for r in rows:
        print(f'Mês: {r[0]} | Quantidade: {r[1]}')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
