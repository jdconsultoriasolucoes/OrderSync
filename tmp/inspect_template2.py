import openpyxl
from pathlib import Path

template_path = Path("e:/OrderSync/backend/assets/template_supra.xlsx")
wb = openpyxl.load_workbook(str(template_path), data_only=True)
ws1 = wb["Cadastro Parte 1"]

print("--- Vendas e Cobranca ---")
for row in ws1.iter_rows(min_row=1, max_row=60, min_col=1, max_col=12):
    for cell in row:
        if isinstance(cell.value, str):
            if any(x in cell.value for x in ["Vendas", "Cobrança", "C/", "P/", "Responsável"]):
                print(f"Cell {cell.coordinate}: {repr(cell.value)}")

print("\n--- Referencias Bancarias ---")
for row in range(32, 38):
    print(f"Bancaria row {row}:", [ws1[f"{c}{row}"].value for c in ["A", "C", "E", "G", "I"]])

print("\n--- Referencias Comerciais ---")
for row in range(38, 44):
    print(f"Comercial row {row}:", [ws1[f"{c}{row}"].value for c in ["A", "E", "G", "I"]])

print("\n--- Bens Imoveis ---")
for row in range(44, 49):
    print(f"Bens row {row}:", [ws1[f"{c}{row}"].value for c in ["A", "H", "J"]])

print("\n--- Plantel ---")
for row in range(49, 54):
    print(f"Plantel row {row}:", [ws1[f"{c}{row}"].value for c in ["A", "F", "H"]])

