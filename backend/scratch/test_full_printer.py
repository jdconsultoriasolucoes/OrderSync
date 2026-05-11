import io
import os
from xlsx2html import xlsx2html
import openpyxl
from xhtml2pdf import pisa

template_path = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def test_conversion():
    try:
        # Preenche um dado fake
        wb = openpyxl.load_workbook(template_path)
        ws = wb["Cadastro Parte 1"]
        ws["A8"] = "CLIENTE TESTE IMPRESSÃO"
        
        # 1. XLSX -> HTML
        html_out = io.StringIO()
        xlsx2html(wb, html_out, sheet="Cadastro Parte 1")
        html_content = html_out.getvalue()
        
        # 2. HTML -> PDF
        pdf_out = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_out)
        
        if pisa_status.err:
            print("Error during PDF conversion")
        else:
            with open("e:\\OrderSync - Dev\\backend\\scratch\\test_printer.pdf", "wb") as f:
                f.write(pdf_out.getvalue())
            print("PDF generated successfully in backend/scratch/test_printer.pdf")
            
    except Exception as e:
        print(f"Conversion failed: {e}")

if __name__ == "__main__":
    test_conversion()
