import pandas as pd
import psycopg2
import sys

INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Historico_de_Pedidos_Faturados_ate_08092026.xlsm'

def generate_report():
    df = pd.read_excel(INPUT_FILE, sheet_name='Banco_Dados', engine='openpyxl')
    
    # Format and clean
    df['Emissão'] = pd.to_datetime(df['Emissão'], errors='coerce')
    data_corte = pd.to_datetime('2026-06-01')
    df = df[df['Emissão'] < data_corte]
    
    df['Preço Unitario'] = pd.to_numeric(df['Preço Unitario'], errors='coerce').fillna(0)
    df['Qtde'] = pd.to_numeric(df['Qtde'], errors='coerce').fillna(0)
    
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
    
    excel_pedidos = {}
    grupos = df.groupby('pedido_supra')
    
    for ped, group in grupos:
        primeira_linha = group.iloc[0]
        subtotal = (group['Qtde'] * group['Preço Unitario']).sum()
        total_pedido = round(subtotal, 2)
        excel_pedidos[str(ped)] = {
            'total': total_pedido,
            'data': primeira_linha['Emissão'].strftime('%d/%m/%Y') if pd.notna(primeira_linha['Emissão']) else 'Sem Data',
            'cliente': str(primeira_linha['Cliente'])
        }
        
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT pedido_supra, SUM(total_pedido), MAX(cliente), MAX(created_at)
        FROM tb_pedidos 
        WHERE observacoes = 'Importação Histórica' 
        AND created_at < '2026-06-01'
        GROUP BY pedido_supra
    """)
    db_pedidos_raw = cur.fetchall()
    db_pedidos = {str(row[0]): {'total': float(row[1]), 'cliente': str(row[2]), 'data': row[3].strftime('%d/%m/%Y') if row[3] else 'Sem Data'} for row in db_pedidos_raw if row[0]}
    
    missing_in_db = []
    diff_values = []
    
    for ped, excel_data in excel_pedidos.items():
        ex_val = excel_data['total']
        if ped not in db_pedidos:
            missing_in_db.append((ped, excel_data['data'], excel_data['cliente'], ex_val))
        else:
            db_val = db_pedidos[ped]['total']
            if abs(ex_val - db_val) > 0.05: 
                diff_values.append((
                    ped, 
                    excel_data['data'], excel_data['cliente'], ex_val, 
                    db_pedidos[ped]['data'], db_pedidos[ped]['cliente'], db_val
                ))
                
    # Format markdown
    md = "# Relatório de Divergências: Histórico de Pedidos\n\n"
    md += "Este relatório documenta as diferenças encontradas entre a nova planilha de histórico e a base de dados oficial, no período anterior a 01/06/2026.\n\n"
    
    md += "## 1. Pedidos Faltantes no Banco de Dados\n"
    md += "Os pedidos abaixo existem apenas na nova planilha (não haviam sido importados anteriormente).\n\n"
    md += "| Pedido | Data | Cliente | Valor (R$) |\n"
    md += "|--------|------|---------|------------|\n"
    for ped, data, cliente, val in missing_in_db:
        md += f"| {ped} | {data} | {cliente} | R$ {val:,.2f} |\n"
        
    md += "\n## 2. Pedidos com Valores Divergentes\n"
    md += "Os pedidos abaixo constam em ambos os locais, mas apresentam valores financeiros diferentes.\n\n"
    md += "| Pedido | Cliente | Data (Planilha) | Valor (Planilha) | Data (Banco) | Valor (Banco) |\n"
    md += "|--------|---------|-----------------|------------------|--------------|---------------|\n"
    for ped, d_ex, c_ex, v_ex, d_db, c_db, v_db in diff_values:
        md += f"| {ped} | {c_ex} | {d_ex} | R$ {v_ex:,.2f} | {d_db} | R$ {v_db:,.2f} |\n"
        
    with open(r'C:\Users\Juan\.gemini\antigravity-ide\brain\f3a05b61-7ecc-49c1-8ac3-437a722934c5\diferencas_historico_faturamento.md', 'w', encoding='utf-8') as f:
        f.write(md)
        
    print("Relatório gerado com sucesso!")

if __name__ == '__main__':
    generate_report()
