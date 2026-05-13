import openpyxl
import os

TEMPLATE_PATH = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def inspect_a34():
    if not os.path.exists(TEMPLATE_PATH):
        print("Template not found")
        return
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    ws2 = wb["Cadastro Parte 2"]
    print(f"Value in [A34]: '{ws2['A34'].value}'")
    print(f"Value in [B34]: '{ws2['B34'].value}'")
    print(f"Merged cells: {ws2.merged_cells}")

if __name__ == "__main__":
    inspect_a34()
