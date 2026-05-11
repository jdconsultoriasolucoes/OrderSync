import openpyxl
import os

template_path = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def inspect_styles():
    wb = openpyxl.load_workbook(template_path)
    ws = wb["Cadastro Parte 1"]
    
    for r in [6, 14, 20]: # Header rows
        cell = ws.cell(row=r, column=1)
        fg = cell.fill.fgColor
        print(f"Row {r}: type={fg.type}, rgb={fg.rgb}, theme={fg.theme}, indexed={fg.indexed}")

if __name__ == "__main__":
    inspect_styles()
