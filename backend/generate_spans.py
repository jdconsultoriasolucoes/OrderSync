
import openpyxl

template_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\NOVA_FICHA_DE_CADASTRO_ALISUL (1).xlsx"
wb = openpyxl.load_workbook(template_path)

def get_spans(sheet_name):
    ws = wb[sheet_name]
    spans = []
    for merge in ws.merged_cells.ranges:
        # reportlab table is (col, row) 0-indexed
        # openpyxl merge is (min_col, min_row, max_col, max_row) 1-indexed
        min_col, min_row, max_col, max_row = merge.min_col-1, merge.min_row-1, merge.max_col-1, merge.max_row-1
        # Filtramos para colunas ate K (index 10)
        if min_col <= 10:
             safe_max_col = min(max_col, 10)
             spans.append(f"('SPAN', ({min_col}, {min_row}), ({safe_max_col}, {max_row}))")
    return spans

print("=== SPANS PÁGINA 1 ===")
print(",\n".join(get_spans("Cadastro Parte 1")))

print("\n=== SPANS PÁGINA 2 ===")
print(",\n".join(get_spans("Cadastro Parte 2")))
