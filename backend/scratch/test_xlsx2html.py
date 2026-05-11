import io
import os
from xlsx2html import xlsx2html
import openpyxl

template_path = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def test_xlsx2html():
    # Preenche um dado fake para testar
    wb = openpyxl.load_workbook(template_path)
    ws = wb["Cadastro Parte 1"]
    ws["A8"] = "Nome do Cliente Teste"
    
    out = io.StringIO()
    xlsx2html(wb, out, sheet="Cadastro Parte 1")
    html_content = out.getvalue()
    
    with open("e:\\OrderSync - Dev\\backend\\scratch\\test_export.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML generated in backend/scratch/test_export.html")

if __name__ == "__main__":
    test_xlsx2html()
