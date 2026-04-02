import pandas as pd
import openpyxl
import sys

file_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\NOVA_FICHA_DE_CADASTRO_ALISUL (1).xlsx"

try:
    # Get sheet names
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    print(f"Sheets: {sheet_names}")

    for sheet in sheet_names:
        print(f"\n--- Mapping Sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        # Just print the head and non-null values to identify fields
        print(f"Shape: {df.shape}")
        # Print actual cells that seem like labels
        for r_idx, row in df.iterrows():
            for c_idx, val in enumerate(row):
                if pd.notnull(val) and isinstance(val, str) and len(val) > 1:
                    print(f"Cell({r_idx+1},{c_idx+1}): {val}")
except Exception as e:
    print(f"Error: {e}")
