import pandas as pd
import sys

file_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\NOVA_FICHA_DE_CADASTRO_ALISUL (1).xlsx"

try:
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    print(f"Sheets: {sheet_names}")

    for sheet in sheet_names:
        print(f"\n======== SHEET: {sheet} ========")
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        
        # Mapping by row and col
        for r in range(df.shape[0]):
            row_data = []
            for c in range(df.shape[1]):
                val = df.iloc[r, c]
                if pd.notnull(val):
                    row_data.append(f"Col{c+1}: [{val}]")
            if row_data:
                print(f"Row {r+1}: {' | '.join(row_data)}")

except Exception as e:
    print(f"Error: {e}")
