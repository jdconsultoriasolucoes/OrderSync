import openpyxl
import os

template_path = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def inspect_print_settings():
    wb = openpyxl.load_workbook(template_path)
    ws = wb["Cadastro Parte 1"]
    
    print(f"Print Area: {ws.print_area}")
    print(f"Page Setup:")
    ps = ws.page_setup
    print(f"  Orientation: {ps.orientation}")
    print(f"  Paper Size: {ps.paperSize}")
    print(f"  Fit to Page: {ps.fitToPage}")
    print(f"  Fit to Width: {ps.fitToWidth}")
    print(f"  Fit to Height: {ps.fitToHeight}")
    
    pm = ws.page_margins
    print(f"Margins: L={pm.left}, R={pm.right}, T={pm.top}, B={pm.bottom}")

if __name__ == "__main__":
    inspect_print_settings()
