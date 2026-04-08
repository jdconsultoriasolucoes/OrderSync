import openpyxl
from pathlib import Path

template_path = Path("e:/OrderSync/backend/assets/template_supra.xlsx")
wb = openpyxl.load_workbook(str(template_path), data_only=True)
ws1 = wb["Cadastro Parte 1"]

for row in range(28, 32):
    for col in "ABCDEFGHIJK":
        cell = ws1[f"{col}{row}"]
        if cell.value:
            print(f"Cell {col}{row}: {cell.value}")
