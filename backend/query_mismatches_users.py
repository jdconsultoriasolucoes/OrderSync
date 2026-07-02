import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()

    cur.execute('''SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_tabela_preco';''')
    cols = [r[0] for r in cur.fetchall()]
    user_col = 'usuario_id' if 'usuario_id' in cols else ('criado_por' if 'criado_por' in cols else ('nome_tabela' if 'nome_tabela' in cols else cols[0]))

    cur.execute(f'''
        SELECT t.{user_col}, COUNT(*)
        FROM tb_tabela_preco t
        WHERE t.codigo_cliente = '125423'
        GROUP BY t.{user_col}
        ORDER BY count DESC
    ''')
    rows = cur.fetchall()
    print('Criadores das Tabelas com código 125423:\n')
    for r in rows:
        print(f'Criador: {r[0]} | Quantidade: {r[1]}')

    conn.close()
except Exception as e:
    print(f'Erro ao conectar: {e}')
