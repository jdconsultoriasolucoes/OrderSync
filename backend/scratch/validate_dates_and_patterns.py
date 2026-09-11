import pandas as pd
import psycopg2

INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Historico_de_Pedidos_Faturados_ate_08092026.xlsm'

def analyze():
    print("Conectando ao banco...")
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()
    
    # 1. VALIDAÇÃO DE DATAS (>= 2026-06-01)
    print("\nLendo Excel para validação de datas e padrões...")
    df = pd.read_excel(INPUT_FILE, sheet_name='Banco_Dados', engine='openpyxl')
    
    df['Emissão'] = pd.to_datetime(df['Emissão'], errors='coerce')
    data_corte = pd.to_datetime('2026-06-01')
    df_new = df[df['Emissão'] >= data_corte]
    
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
            
    df_new['pedido_supra'] = df_new['Pedido'].apply(format_supra_or_nota)
    
    excel_dates = {}
    grupos = df_new.groupby('pedido_supra')
    for ped, group in grupos:
        dt = group.iloc[0]['Emissão']
        if pd.notna(dt):
            excel_dates[str(ped)] = dt.strftime('%Y-%m-%d')
            
    cur.execute("""
        SELECT pedido_supra, created_at AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo'
        FROM tb_pedidos 
        WHERE created_at >= '2026-06-01'
    """)
    db_dates_raw = cur.fetchall()
    
    date_mismatches = []
    for ped, db_dt in db_dates_raw:
        ped_str = str(ped)
        if ped_str in excel_dates:
            db_date_str = db_dt.strftime('%Y-%m-%d') if db_dt else None
            ex_date_str = excel_dates[ped_str]
            if db_date_str != ex_date_str:
                date_mismatches.append((ped_str, ex_date_str, db_date_str))
                
    print(f"-> Incompatibilidades de data encontradas: {len(date_mismatches)}")
    for ped, ex, db in date_mismatches[:5]:
        print(f"Pedido {ped}: Excel={ex} | DB={db}")
        
    # 2. INVESTIGAÇÃO DE PADRÕES (Diferença no pedido 2023004285)
    print("\nAnalisando o pedido divergente antigo 2023004285...")
    df_old = df[df['Pedido'].apply(format_supra_or_nota) == '2023004285']
    if not df_old.empty:
        ex_frete = df_old['Frete(TO)'].iloc[0]
        ex_itens = (df_old['Qtde'] * pd.to_numeric(df_old['Preço Unitario'], errors='coerce').fillna(0)).sum()
        ex_total = ex_itens
        if ex_frete > 0:
            # no script preparar_ingestao, frete não soma no total_pedido?
            ex_total_com_frete = ex_itens + ex_frete # logic?
            print(f"EXCEL 2023004285 -> Itens: {ex_itens:.2f} | Frete(TO): {ex_frete:.2f}")
            
    cur.execute("""
        SELECT total_pedido, total_sem_frete, total_com_frete, frete_total, usar_valor_com_frete 
        FROM tb_pedidos 
        WHERE pedido_supra = '2023004285'
    """)
    db_old = cur.fetchone()
    if db_old:
        print(f"DB 2023004285 -> Total: {db_old[0]} | Sem Frete: {db_old[1]} | Com Frete: {db_old[2]} | Frete_Total: {db_old[3]} | Usar Frete: {db_old[4]}")
        
    # Also check if any old logic was "Total = Itens + Frete" vs new logic "Total = Itens"
    cur.execute("SELECT COUNT(*) FROM tb_pedidos WHERE total_pedido = total_com_frete AND frete_total > 0 AND created_at < '2026-06-01'")
    old_freight_logic = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tb_pedidos WHERE total_pedido = total_sem_frete AND frete_total > 0 AND created_at >= '2026-06-01'")
    new_freight_logic = cur.fetchone()[0]
    print(f"Pedidos antigos onde total incluiu frete: {old_freight_logic}")
    print(f"Pedidos novos onde total não incluiu frete: {new_freight_logic}")

if __name__ == '__main__':
    analyze()
