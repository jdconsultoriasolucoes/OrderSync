import pandas as pd

file_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\relatorio de importação\estoque.xlsx"
df = pd.read_excel(file_path)

# Drop rows where 'Produto' is null
df_clean = df.dropna(subset=['Produto'])

# Select relevant columns: Col 0 (A), Col 1 (B), Col 5 (F), Col 6 (G), Col 7 (H), Col 10 (K)
cols = [0, 1, 5, 6, 7, 10]
col_names = [df.columns[i] for i in cols]

print("Selected columns:")
for i in cols:
    print(f"Col {i} (Letter {chr(65+i)}): {df.columns[i]}")

print("\nSample rows (first 10):")
print(df_clean[col_names].head(10).to_string(index=False))
