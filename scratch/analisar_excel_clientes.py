import pandas as pd
import os

file_path = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\base_clientes_2804.xlsx'

if os.path.exists(file_path):
    try:
        # Lendo pulando a primeira linha (título) para pegar o cabeçalho real
        df = pd.read_excel(file_path, header=1, nrows=5)
        print("Colunas encontradas no Excel (Total: {}):".format(len(df.columns)))
        for i, col in enumerate(df.columns):
            print(f"{i}: {col}")
        
        print("\nPrimeiras 2 linhas de dados:")
        print(df.head(2))
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
else:
    print(f"Arquivo não encontrado: {file_path}")
