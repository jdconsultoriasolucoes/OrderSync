import openpyxl
from pathlib import Path

template_path = Path("e:/OrderSync/backend/assets/template_supra.xlsx")
wb = openpyxl.load_workbook(str(template_path), data_only=True)
ws1 = wb["Cadastro Parte 1"]

print("--- Consumo Mensal Cells in Plantel ---")
for row in range(50, 54):
    for col in "ABCDEFGHIJK":
        c = ws1[f"{col}{row}"]
        if c.value:
            print(f"Cell {col}{row}: {c.value}")

print("\n--- Tipo de Cliente Cells ---")
cells = ["C17", "E18", "E17", "G18", "G17", "I18", "I17", "C18"]
for coord in cells:
    val = ws1[coord].value
    print(f"Cell {coord}: {repr(val)}")
