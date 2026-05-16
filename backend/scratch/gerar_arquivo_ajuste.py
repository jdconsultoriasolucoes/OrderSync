import pandas as pd
import os
from datetime import datetime

# Caminhos (Baseado no seu script original)
INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Tb_ingestao_historico_pedido.xlsx'
OUTPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\ajuste_datas_pedidos.csv'

def gerar_csv_ajuste():
    print(f"Lendo Excel: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print("Erro: Arquivo original não encontrado.")
        return

    # Lendo apenas as colunas necessárias para economizar memória
    cols_to_read = ['Pedido', 'Nota', 'Emissão']
    df = pd.read_excel(INPUT_FILE, usecols=cols_to_read)
    
    # Remover duplicatas de pedidos (já que o original tem itens repetidos por pedido)
    df = df.drop_duplicates(subset=['Pedido'])

    print("Formatando datas...")
    # Formata a data para string ISO literal (Americano)
    def format_dt(val):
        if pd.isna(val): return None
        return val.strftime('%Y-%m-%d %H:%M:%S')

    df['confirmado_em'] = df['Emissão'].apply(format_dt)
    df['created_at'] = df['Emissão'].apply(format_dt)
    
    # Renomear para facilitar o JOIN no SQL
    df_final = df[['Pedido', 'Nota', 'confirmado_em', 'created_at']].rename(columns={
        'Pedido': 'pedido_supra',
        'Nota': 'nota_fiscal'
    })

    print(f"Salvando arquivo de ajuste: {OUTPUT_FILE}")
    df_final.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8-sig')
    print("Sucesso! Arquivo pronto para uso no banco.")

if __name__ == "__main__":
    gerar_csv_ajuste()
