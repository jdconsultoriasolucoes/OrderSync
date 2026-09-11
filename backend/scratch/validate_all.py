import pandas as pd
import psycopg2

INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Historico_de_Pedidos_Faturados_ate_08092026.xlsm'

def validate_all():
    print("1. Lendo arquivo original Excel (Isso pode demorar um pouco)...")
    df = pd.read_excel(INPUT_FILE, sheet_name='Banco_Dados', engine='openpyxl')
    
    print("Processando colunas...")
    df['Preço Unitario'] = pd.to_numeric(df['Preço Unitario'], errors='coerce').fillna(0)
    df['Qtde'] = pd.to_numeric(df['Qtde'], errors='coerce').fillna(0)
    df['Frete(TO)'] = pd.to_numeric(df['Frete(TO)'], errors='coerce').fillna(0)
    
    # Calcular totais do arquivo agrupando por pedido para somar o frete apenas uma vez
    total_excel_qtde = df['Qtde'].sum()
    
    grupos = df.groupby('Pedido')
    total_excel_financeiro = 0
    
    for _, group in grupos:
        primeira_linha = group.iloc[0]
        subtotal_itens = (group['Qtde'] * group['Preço Unitario']).sum()
        
        frete = primeira_linha['Frete(TO)']
        if frete > 0:
            total_pedido = round(subtotal_itens, 2) # a logica do script original para frete nao soma o frete_to no total_pedido, ele coloca total_pedido = round(total_sem_frete, 2)
            # Wait, script original line 184:
            # "total_sem_frete": 0 if frete > 0 else round(total_sem_frete, 2)
            # "total_com_frete": round(total_sem_frete, 2) if frete > 0 else 0
            # "total_pedido": round(total_sem_frete, 2)
            # Entao total_pedido eh sempre round(subtotal_itens, 2)
        else:
            total_pedido = round(subtotal_itens, 2)
            
        total_excel_financeiro += total_pedido

    print(f"\n--- TOTAL DO ARQUIVO EXCEL COMPLETO ---")
    print(f"Total Financeiro: R$ {total_excel_financeiro:,.2f}")
    print(f"Quantidade: {total_excel_qtde:,.2f}")
    
    print("\n2. Consultando o Banco de Produção...")
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()
    
    # Historico eh marcado com observacoes = 'Importação Histórica'
    cur.execute("SELECT SUM(total_pedido) FROM tb_pedidos WHERE observacoes = 'Importação Histórica'")
    total_db_financeiro = cur.fetchone()[0] or 0
    
    cur.execute("SELECT SUM(quantidade) FROM tb_pedidos_itens WHERE id_pedido IN (SELECT id_pedido FROM tb_pedidos WHERE observacoes = 'Importação Histórica')")
    total_db_qtde = cur.fetchone()[0] or 0
    
    print(f"\n--- TOTAL NO BANCO DE PRODUÇÃO ---")
    print(f"Total Financeiro: R$ {total_db_financeiro:,.2f}")
    print(f"Quantidade: {total_db_qtde:,.2f}")
    
    diff_fin = abs(total_excel_financeiro - float(total_db_financeiro))
    diff_qtd = abs(total_excel_qtde - float(total_db_qtde))
    
    print(f"\n--- DIFERENÇA ---")
    print(f"Financeiro: R$ {diff_fin:,.2f}")
    print(f"Quantidade: {diff_qtd:,.2f}")

if __name__ == '__main__':
    validate_all()
