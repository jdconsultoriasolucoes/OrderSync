import os
import pandas as pd

file_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\relatorio de importação\estoque.xlsx"

print("Checking file path:", file_path)
if not os.path.exists(file_path):
    print("File does not exist!")
    # Let's list files in the directory to see if there is a typo or if the path is slightly different
    dir_path = os.path.dirname(file_path)
    if os.path.exists(dir_path):
        print("Directory exists. Files inside:")
        print(os.listdir(dir_path))
    else:
        print("Directory does not exist either:", dir_path)
else:
    print("File exists! Reading content...")
    try:
        df = pd.read_excel(file_path)
        print("Columns found:")
        for idx, col in enumerate(df.columns):
            print(f"Col {idx} (Letter {chr(65+idx) if idx < 26 else '?'}) name: {repr(col)}")
        print("\nFirst 5 rows:")
        print(df.head(5))
    except Exception as e:
        print("Error reading Excel:", e)
