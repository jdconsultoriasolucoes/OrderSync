import pandas as pd
import psycopg2

INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Historico_de_Pedidos_Faturados_ate_08092026.xlsm'

def find_diff():
    print("1. Lendo arquivo original Excel...")
    df = pd.read_excel(INPUT_FILE, sheet_name='Banco_Dados', engine='openpyxl')
    
    # Format and clean
    df['Emissão'] = pd.to_datetime(df['Emissão'], errors='coerce')
    
    # Filtrar apenas antes de 2026-06-01, pois sabemos que depois disso esta igual
    data_corte = pd.to_datetime('2026-06-01')
    df = df[df['Emissão'] < data_corte]
    
    df['Preço Unitario'] = pd.to_numeric(df['Preço Unitario'], errors='coerce').fillna(0)
    df['Qtde'] = pd.to_numeric(df['Qtde'], errors='coerce').fillna(0)
    
    # Format Pedido (pedido_supra)
    def format_supra_or_nota(val):
        if pd.isna(val):
            return ""
        try:
            float_val = float(val)
            if float_val.is_integer():
                return str(int(float_val))
            return str(float_val)
        except:
            return str(val).strip()
            
    df['pedido_supra'] = df['Pedido'].apply(format_supra_or_nota)
    
    # Calculate order totals in Excel
    excel_pedidos = {}
    grupos = df.groupby('pedido_supra')
    
    for ped, group in grupos:
        primeira_linha = group.iloc[0]
        subtotal = (group['Qtde'] * group['Preço Unitario']).sum()
        total_pedido = round(subtotal, 2)
        excel_pedidos[str(ped)] = {
            'total': total_pedido,
            'data': primeira_linha['Emissão'].strftime('%Y-%m-%d') if pd.notna(primeira_linha['Emissão']) else 'Sem Data'
        }
        
    print(f"Total de pedidos únicos no Excel (antes de 01/06/2026): {len(excel_pedidos)}")
    
    print("2. Consultando o Banco de Dados...")
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()
    
    # Get all historical orders before 2026-06-01
    cur.execute("""
        SELECT pedido_supra, SUM(total_pedido) 
        FROM tb_pedidos 
        WHERE observacoes = 'Importação Histórica' 
        AND created_at < '2026-06-01'
        GROUP BY pedido_supra
    """)
    db_pedidos_raw = cur.fetchall()
    db_pedidos = {str(row[0]): float(row[1]) for row in db_pedidos_raw if row[0]}
    
    print(f"Total de pedidos únicos no DB (antes de 01/06/2026): {len(db_pedidos)}")
    
    print("\n3. Comparando...")
    missing_in_db = []
    diff_values = []
    
    for ped, excel_data in excel_pedidos.items():
        ex_val = excel_data['total']
        if ped not in db_pedidos:
            missing_in_db.append((ped, ex_val, excel_data['data']))
        else:
            db_val = db_pedidos[ped]
            if abs(ex_val - db_val) > 0.05: # tolerance for floating point
                diff_values.append((ped, ex_val, db_val, excel_data['data']))
                
    missing_in_excel = []
    for ped, db_val in db_pedidos.items():
        if ped not in excel_pedidos:
            missing_in_excel.append((ped, db_val))

    print(f"\n--- RESULTADOS ---")
    print(f"Pedidos no Excel que NÃO estão no Banco (Faltando no DB): {len(missing_in_db)}")
    if missing_in_db:
        print("Exemplos dos que estão faltando no DB:")
        for ped, val, data in missing_in_db[:10]:
            print(f" - Pedido {ped} | Data: {data} | Valor: R$ {val:.2f}")
            
    print(f"\nPedidos com valor diferente: {len(diff_values)}")
    if diff_values:
        for ped, ex_val, db_val, data in diff_values[:10]:
            print(f" - Pedido {ped} | Data: {data} | Excel: {ex_val:.2f} | DB: {db_val:.2f}")
            
    print(f"\nPedidos no DB que NÃO estão no Excel: {len(missing_in_excel)}")
    if missing_in_excel:
        for ped, val in missing_in_excel[:5]:
            print(f" - Pedido {ped} | Valor DB: {val:.2f}")

if __name__ == '__main__':
    find_diff()
