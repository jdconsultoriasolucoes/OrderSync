import sys
import openpyxl
import traceback

def test():
    wb = openpyxl.load_workbook('e:/OrderSync/backend/assets/template_supra.xlsx')
    ws1 = wb['Cadastro Parte 1']
    ws2 = wb['Cadastro Parte 2']
    
    # helper for checking
    def safe_assign(ws, coord, value):
        try:
            cell = ws[coord]
            cell.value = value
        except Exception as e:
            print(f"CRASH NO COORD {ws.title} - {coord}: {e}")
            raise

    assignments = [
        (ws1, "A8"), (ws1, "A9"), (ws1, "A10"), (ws1, "A11"), (ws1, "E11"), (ws1, "A12"),
        (ws1, "A13"), (ws1, "E13"),
        # checkboxes
        (ws1, "C17"), (ws1, "E18"), (ws1, "E17"), (ws1, "G18"), (ws1, "G17"), (ws1, "I18"),
        (ws1, "I17"), (ws1, "C18"),
        # faturamento/entrega
        (ws1, "A21"), (ws1, "I21"), (ws1, "A22"), (ws1, "F22"), (ws1, "I22"),
        (ws1, "A25"), (ws1, "I25"), (ws1, "A26"), (ws1, "F26"), (ws1, "I26"),
        # vendas e cob
        (ws1, "A29"), (ws1, "F29"), (ws1, "A30"), (ws1, "F30"),
        # local e data
        (ws1, "C61"),
    ]
    
    for i in range(4):
        r = 34 + i
        assignments.extend([(ws1, f"A{r}"), (ws1, f"C{r}"), (ws1, f"E{r}")])
    for i in range(4):
        r = 40 + i
        assignments.extend([(ws1, f"A{r}"), (ws1, f"E{r}"), (ws1, f"G{r}"), (ws1, f"I{r}")])
    for i in range(3):
        r = 46 + i
        assignments.extend([(ws1, f"A{r}"), (ws1, f"C{r}"), (ws1, f"F{r}"), (ws1, f"H{r}"), (ws1, f"J{r}")])
    for i in range(3):
        r = 57 + i
        assignments.extend([(ws1, f"A{r}"), (ws1, f"E{r}"), (ws1, f"G{r}"), (ws1, f"I{r}")])
    for i in range(3):
        r = 51 + i
        assignments.extend([(ws1, f"A{r}"), (ws1, f"F{r}"), (ws1, f"H{r}"), (ws1, f"J{r}")])

    # aba 2
    assignments.extend([
        (ws2, "E7"), (ws2, "E8"), (ws2, "C14"), (ws2, "C15"), (ws2, "C16"),
        (ws2, "C20"), (ws2, "C21"),
        (ws2, "E25"), (ws2, "H25"), (ws2, "E26"), (ws2, "H26"),
        (ws2, "E27"), (ws2, "H27"), (ws2, "D35"), (ws2, "A41"), (ws2, "A42"), (ws2, "A43")
    ])

    for ws, coord in assignments:
        try:
            safe_assign(ws, coord, "teste")
        except:
            return

    print("Nenhum erro de MergedCell encontrado nas coordenadas principais!")

test()
