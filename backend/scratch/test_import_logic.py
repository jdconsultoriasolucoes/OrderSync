import sys
import os
import pandas as pd
import unicodedata

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def normalize_text(text_val):
    if pd.isna(text_val) or text_val is None:
        return ""
    val_str = str(text_val)
    normalized = unicodedata.normalize('NFKD', val_str).encode('ascii', 'ignore').decode('utf-8')
    return normalized.lower().strip()

def clean_numeric_code(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if not val_str:
        return ""
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    val_str = val_str.replace(".", "")
    return val_str

def clean_currency(val):
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace("R$", "").strip()
    if not val_str:
        return 0.0
    if "," in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def find_column(df, keywords):
    for col in df.columns:
        norm_col = normalize_text(col)
        if all(kw in norm_col for kw in keywords):
            return col
    return None

file_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Entrada_Pedidos.xlsm"

print(f"Lendo {file_path}...")
try:
    df_bd = pd.read_excel(file_path, sheet_name="Banco_Dados", skiprows=1)
    df_danfes = pd.read_excel(file_path, sheet_name="Danfes")

    col_pedido = find_column(df_bd, ["pedido"]) 
    col_emissao = find_column(df_bd, ["emissao"])
    col_peso = find_column(df_bd, ["peso"])
    col_valor = find_column(df_bd, ["valor", "pedido"])
    col_danfe = find_column(df_bd, ["danfe"])
    col_codigo = find_column(df_bd, ["codigo"])

    print("Colunas encontradas dinamicamente na aba Banco_Dados:")
    print(f"Pedido: {col_pedido}")
    print(f"Emissão: {col_emissao}")
    print(f"Peso: {col_peso}")
    print(f"Valor do Pedido: {col_valor}")
    print(f"Danfe: {col_danfe}")
    print(f"Codigo(Cliente): {col_codigo}")

    df_danfes_clean = pd.DataFrame({
        'pedido_supra': df_danfes.iloc[:, 8].apply(clean_numeric_code),
        'status_excel': df_danfes.iloc[:, 10].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    })
    df_danfes_clean = df_danfes_clean[df_danfes_clean['pedido_supra'] != ""]

    print(f"\nExtraídos {len(df_danfes_clean)} pedidos com número válido da aba Danfes.")

    print("\nAmostra das 3 primeiras linhas consolidadas:")
    count = 0
    for index, row in df_bd.iterrows():
        if count >= 3: break
        pedido_val = row.get(col_pedido) if col_pedido else None
        pedido_supra = clean_numeric_code(pedido_val)
        
        if not pedido_supra or str(pedido_supra).lower() == 'nan':
            continue
            
        peso = clean_currency(row.get(col_peso)) if col_peso else 0.0
        valor_pedido = clean_currency(row.get(col_valor)) if col_valor else 0.0
        
        danfes_row = df_danfes_clean[df_danfes_clean['pedido_supra'] == pedido_supra]
        status_excel = danfes_row['status_excel'].iloc[0] if not danfes_row.empty else ""
        
        print(f" - Pedido {pedido_supra}: Peso={peso}, Valor={valor_pedido}, Status Danfes='{status_excel}'")
        count += 1
except Exception as e:
    print(f"Erro no teste: {e}")
