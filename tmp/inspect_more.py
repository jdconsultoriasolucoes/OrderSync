import openpyxl
from pathlib import Path

template_path = Path("e:/OrderSync/backend/assets/template_supra.xlsx")
wb = openpyxl.load_workbook(str(template_path), data_only=True)
ws1 = wb["Cadastro Parte 1"]

for row in ws1.iter_rows(min_row=1, max_row=60, min_col=1, max_col=12):
    for cell in row:
        if isinstance(cell.value, str):
            val = cell.value.strip().lower()
            if any(x in val for x in ["sócio", "diretor", "indicaç", "grupo"]):
                print(f"[Cadastro Parte 1] {cell.coordinate}: {cell.value}")
