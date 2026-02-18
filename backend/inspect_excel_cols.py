import pandas as pd
import sys

file_path = r"E:\Projeto Sistema pedidos\extrações\Tabela_preço_layout.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print("Sheets found:", xl.sheet_names)
    
    # Try to find a matching sheet or use the first one
    sheet_name = None
    for s in xl.sheet_names:
        if 'tabela' in s.lower() and 'pre' in s.lower():
            sheet_name = s
            break
    
    if not sheet_name:
        sheet_name = xl.sheet_names[0]
        
    print(f"Inspecting sheet: {sheet_name}")
    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
    print("Columns found:")
    for col in df.columns:
        print(f"- {col}")
except Exception as e:
    print(f"Error reading excel: {e}")
