
import pandas as pd
from sqlalchemy import create_engine, text
import sys

# Constants
DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
INPUT_FILE = r"E:\Projeto Sistema pedidos\extrações\Tabela_preco_preenchida_v5.xlsx"
OUTPUT_SQL = r"E:\Projeto Sistema pedidos\extrações\insert_tabela_preco.sql"

try:
    engine = create_engine(DB_URL)
    conn = engine.connect()
    
    # Get Max ID Tabela to increment
    result = conn.execute(text("SELECT COALESCE(MAX(id_tabela), 0) FROM tb_tabela_preco"))
    max_id_tabela = result.scalar()
    next_id_tabela = max_id_tabela + 1
    
    # Get Max ID Linha to increment (for explicit insertion)
    result_linha = conn.execute(text("SELECT COALESCE(MAX(id_linha), 0) FROM tb_tabela_preco"))
    max_id_linha = result_linha.scalar()
    
    print(f"Próximo id_tabela será: {next_id_tabela}")
    print(f"Último id_linha no banco: {max_id_linha}. Iniciando inserts a partir de: {max_id_linha + 1}")
    
    conn.close()
except Exception as e:
    print(f"Erro ao conectar banco: {e}")
    # Fallback if DB fails
    next_id_tabela = 9999
    max_id_linha = 0
    
try:
    print(f"Lendo: {INPUT_FILE}")
    df = pd.read_excel(INPUT_FILE)
    
    # Generate SQL
    # Columns matching DB
    db_cols = [
        'id_linha', 'id_tabela', 'nome_tabela', 'fornecedor', 'codigo_cliente', 'cliente',
        'codigo_produto_supra', 'descricao_produto', 'embalagem',
        'peso_liquido', 'valor_produto', 'comissao_aplicada', 'ajuste_pagamento',
        'descricao_fator_comissao', 'codigo_plano_pagamento',
        'markup', 'valor_final_markup', 'valor_s_frete_markup',
        'valor_frete_aplicado', 'frete_kg', 'valor_frete', 'valor_s_frete',
        'grupo', 'departamento',
        'ipi', 'icms_st', 'iva_st', 'calcula_st', 'ativo'
    ]
    
    # Assign id_tabela
    # We assume all rows in this file belong to the SAME new table or split by nome_tabela?
    # Let's map unique nome_tabela to new IDs
    unique_names = df['nome_tabela'].unique()
    name_id_map = {}
    current_tabela_id = next_id_tabela
    for name in unique_names:
        name_id_map[name] = current_tabela_id
        current_tabela_id += 1
        
    df['id_tabela'] = df['nome_tabela'].map(name_id_map)
    
    # Sort by Table ID to ensure sequential inserts block by block
    df = df.sort_values(by=['id_tabela', 'descricao_produto'])
    
    # Assign id_linha sequentially AFTER sorting
    # We ignore the 'id_linha' from Excel and generate continuous ones
    df['id_linha'] = range(max_id_linha + 1, max_id_linha + 1 + len(df))
    
    # Handle missing/default cols
    if 'ativo' not in df.columns:
        df['ativo'] = True
        
    # Helper to clean strings and format SQL values
    def fmt_val(v):
        if pd.isna(v): return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
             return str(v)
        # String fallback
        clean = str(v).replace("'", "''")
        return f"'{clean}'"

    print(f"Gerando SQL para {len(df)} linhas...")
    
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Script gerado automaticamente\n")
        f.write(f"-- Inicio id_linha: {max_id_linha + 1}\n")
        f.write(f"-- Inicio id_tabela: {next_id_tabela}\n\n")
        
        # Split into chunks to avoid huge query limits if needed, but INSERT usually handles many values.
        # Postgres supports multi-value insert.
        # Let's do batches of 100 rows.
        
        batch_size = 100
        total_rows = len(df)
        
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            
            cols_str = ", ".join(db_cols)
            f.write(f"INSERT INTO tb_tabela_preco ({cols_str}) VALUES \n")
            
            values_list = []
            for _, row in batch.iterrows():
                row_vals = []
                for col in db_cols:
                    val = row.get(col)
                    # Specific fixes
                    if col == 'calcula_st':
                        # Ensure boolean
                        val = bool(val) if not pd.isna(val) else False
                    
                    if col == 'descricao_fator_comissao' and pd.isna(val):
                        val = ""
                    
                    row_vals.append(fmt_val(val))
                
                vals_str = "(" + ", ".join(row_vals) + ")"
                values_list.append(vals_str)
            
            f.write(",\n".join(values_list))
            f.write(";\n\n")
            
        # IMPORTANT: Fix Sequence after explicit ID inserts
        # Write SQL footer
        f.write("\n-- Corrigir a sequência do id_linha para evitar conflitos futuros\n")
        f.write("SELECT setval('tb_tabela_preco_v2_id_linha_seq', (SELECT MAX(id_linha) FROM tb_tabela_preco));\n")
            
    print(f"SQL gerado em: {OUTPUT_SQL}")

except Exception as e:
    print(f"Erro ao gerar SQL: {e}")
    import traceback
    traceback.print_exc()

