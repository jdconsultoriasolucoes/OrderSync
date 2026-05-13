import openpyxl
import os

TEMPLATE_PATH = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def inspect_vendor_cobranca():
    if not os.path.exists(TEMPLATE_PATH):
        print("Template not found")
        return
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    ws2 = wb["Cadastro Parte 2"]
    print(f"Value in [D34]: '{ws2['D34'].value}'")
    print(f"Value in [H34]: '{ws2['H34'].value}'")

if __name__ == "__main__":
    inspect_vendor_cobranca()
