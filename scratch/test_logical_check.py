import psycopg2
import pandas as pd
import datetime

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require"

def run_simulation():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # 1. Buscar um pedido elegível para teste que tenha pedido_supra e nota_fiscal
    cursor.execute("""
        SELECT pedido_supra, nota_fiscal, total_pedido, peso_total_kg, codigo_cliente, status, data_faturamento 
        FROM public.tb_pedidos 
        WHERE pedido_supra IS NOT NULL AND nota_fiscal IS NOT NULL AND nota_fiscal <> ''
        LIMIT 1;
    """)
    row = cursor.fetchone()
    if not row:
        print("Aviso: Nenhum pedido elegível com nota fiscal encontrado no banco de dados para simulação lógica.")
        cursor.close()
        conn.close()
        return

    pedido_supra, nf_db, total_db, peso_db, cod_cli_db, status_db, data_fat_db = row
    print("--- Dados do Pedido Selecionado no Banco ---")
    print(f"Pedido Supra: {pedido_supra}")
    print(f"Nota Fiscal: {nf_db}")
    print(f"Total: {total_db}")
    print(f"Peso: {peso_db}")
    print(f"Cliente: {cod_cli_db}")
    print(f"Status: {status_db}")
    print(f"Data Fat: {data_fat_db}")
    
    # 2. Simular dados vindos da Planilha (Cenário: 100% igual -> SEM_ALTERACAO)
    # Valores extraídos da planilha:
    danfe = nf_db
    valor_pedido = float(total_db)
    peso = float(peso_db)
    codigo_cliente = str(cod_cli_db).strip()
    # Se terminar com .0, remove igual fazemos no backend
    if codigo_cliente.endswith(".0"):
        codigo_cliente = codigo_cliente[:-2]
    codigo_cliente = codigo_cliente.replace(".", "")
    
    status_excel = "pedido faturado" # Mapeia para FATURADO_SUPRA no backend se houver danfe
    status_novo_pedido = 'FATURADO_SUPRA' if danfe else None
    
    data_danfe_dt = data_fat_db # Simulando a mesma data
    
    # Executar a verificação exatamente como foi codificada no backend
    is_nf_same = (nf_db or "") == danfe
    is_val_same = abs(valor_pedido - float(total_db)) <= 0.01
    is_peso_same = abs(peso - float(peso_db)) <= 0.01
    
    # clean code do cliente no banco
    cod_cli_db_clean = str(cod_cli_db).strip()
    if cod_cli_db_clean.endswith(".0"):
        cod_cli_db_clean = cod_cli_db_clean[:-2]
    cod_cli_db_clean = cod_cli_db_clean.replace(".", "")
    is_cli_same = cod_cli_db_clean == codigo_cliente
    
    is_status_same = (status_novo_pedido is None) or (status_db == status_novo_pedido)
    
    # Comparação de data
    def is_same_date(dt1, dt2):
        t1 = pd.to_datetime(dt1) if pd.notna(dt1) else None
        t2 = pd.to_datetime(dt2) if pd.notna(dt2) else None
        if t1 is None and t2 is None:
            return True
        if t1 is None or t2 is None:
            return False
        return t1.date() == t2.date()
        
    is_date_same = is_same_date(data_danfe_dt, data_fat_db)
    
    print("\n--- Resultados dos Checks Individuais ---")
    print(f"NF idêntica: {is_nf_same}")
    print(f"Valor idêntico: {is_val_same}")
    print(f"Peso idêntico: {is_peso_same}")
    print(f"Cliente idêntico: {is_cli_same}")
    print(f"Status esperado: {is_status_same}")
    print(f"Data faturamento idêntica: {is_date_same}")
    
    if is_nf_same and is_val_same and is_peso_same and is_cli_same and is_status_same and is_date_same:
        print("\nResultado lógico da Simulação: >>> SEM_ALTERACAO <<< (Sucesso!)")
    else:
        print("\nResultado lógico da Simulação: Requer Alteração (Divergente)")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_simulation()
