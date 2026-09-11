import pandas as pd
import psycopg2

csv_pedidos = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados\tb_pedidos_ingestao.csv'
csv_itens = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados\tb_pedidos_itens_ingestao.csv'

df_p = pd.read_csv(csv_pedidos, sep=';')
df_i = pd.read_csv(csv_itens, sep=';')

total_csv_pedido = df_p['total_pedido'].sum()
total_csv_qtde = df_i['quantidade'].sum()

print('--- DADOS DOS ARQUIVOS (INGESTAO) ---')
print(f'Total Financeiro: R$ {total_csv_pedido:,.2f}')
print(f'Quantidade Faturada: {total_csv_qtde:,.2f}')

conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
cur = conn.cursor()

cur.execute("SELECT SUM(total_pedido) FROM tb_pedidos WHERE created_at >= '2026-06-01'")
total_db_pedido = cur.fetchone()[0] or 0

cur.execute("SELECT SUM(quantidade) FROM tb_pedidos_itens WHERE id_pedido IN (SELECT id_pedido FROM tb_pedidos WHERE created_at >= '2026-06-01')")
total_db_qtde = cur.fetchone()[0] or 0

print('\n--- DADOS NO BANCO DE PRODUÇÃO ---')
print(f'Total Financeiro: R$ {total_db_pedido:,.2f}')
print(f'Quantidade Faturada: {total_db_qtde:,.2f}')

diff_fin = abs(total_csv_pedido - float(total_db_pedido))
diff_qtd = abs(total_csv_qtde - float(total_db_qtde))

print('\n--- DIFERENÇA ---')
print(f'Financeiro: R$ {diff_fin:,.2f}')
print(f'Quantidade: {diff_qtd:,.2f}')
