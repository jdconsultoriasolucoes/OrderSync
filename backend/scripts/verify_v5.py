import pandas as pd
import os

FILE_PATH = r"E:\Projeto Sistema pedidos\extrações\Tabela_preco_preenchida_v5.xlsx"

if not os.path.exists(FILE_PATH):
    print(f"File not found: {FILE_PATH}")
else:
    try:
        df = pd.read_excel(FILE_PATH)
        print("Columns:", df.columns.tolist())
        print("\nFirst 5 rows of `valor_frete` and `valor_s_frete`:")
        if 'valor_frete' in df.columns and 'valor_s_frete' in df.columns:
            print(df[['valor_frete', 'valor_s_frete']].head())
            
            # Check for nulls
            nulls_frete = df['valor_frete'].isnull().sum()
            nulls_s_frete = df['valor_s_frete'].isnull().sum()
            print(f"\nNull values in valor_frete: {nulls_frete}")
            print(f"Null values in valor_s_frete: {nulls_s_frete}")
            
            # Check for zeros
            zeros_frete = (df['valor_frete'] == 0).sum()
            zeros_s_frete = (df['valor_s_frete'] == 0).sum()
            print(f"Zero values in valor_frete: {zeros_frete}")
            print(f"Zero values in valor_s_frete: {zeros_s_frete}")
        else:
            print("Columns `valor_frete` or `valor_s_frete` not found in dataframe.")
            
    except Exception as e:
        print(f"Error reading file: {e}")
