import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"
INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Tb_ingestao_historico_pedido.xlsx'

def check_db_and_excel():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id_pedido, pedido_supra, nota_fiscal FROM tb_pedidos WHERE id_pedido = 9442;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        print("Pedido 9442 não encontrado no banco.")
        return
        
    id_ped, supra, nota = row
    print(f"DB -> ID: {id_ped}, pedido_supra: {supra}, nota_fiscal: {nota}")
    
    if os.path.exists(INPUT_FILE):
        df = pd.read_excel(INPUT_FILE, sheet_name='Planilha1')
        match = df[df['Pedido'].astype(str).str.contains(str(supra))]
        if match.empty:
            print("Não encontrado no Excel com pedido_supra:", supra)
        else:
            print("\nLinhas correspondentes no Excel:")
            print(match[['Pedido', 'Nota', 'Produto', 'Qtde', 'Preço Unitario', 'Frete(TO)']].to_string())
    else:
        print("Excel não encontrado")

if __name__ == '__main__':
    check_db_and_excel()
