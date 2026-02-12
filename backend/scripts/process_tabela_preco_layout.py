
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
import os
import sys
import math

def safe_float(val):
    if val is None: return 0.0
    try:
        f = float(val)
        if math.isnan(f): return 0.0
        return f
    except:
        return 0.0

# Database Connection
DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
INPUT_FILE = r"E:\Projeto Sistema pedidos\extrações\Tabela_preço_layout.xlsx"
OUTPUT_FILE = r"E:\Projeto Sistema pedidos\extrações\Tabela_preco_preenchida_v5.xlsx"

# Connect to DB
try:
    engine = create_engine(DB_URL)
    conn = engine.connect()
    print("Conectado ao banco de dados.")
except Exception as e:
    print(f"Erro ao conectar no banco: {e}")
    sys.exit(1)

# Load Data
try:
    print(f"Lendo arquivo: {INPUT_FILE}")
    df_input = pd.read_excel(INPUT_FILE, sheet_name='Tabela_preco')
except Exception as e:
    print(f"Erro ao ler Excel: {e}")
    conn.close()
    sys.exit(1)

# Pre-fetch Products & Taxes
print("Carregando produtos e impostos...")
sql_prods = text("""
    SELECT 
        p.codigo_supra, 
        p.nome_produto, 
        p.embalagem_venda, 
        p.peso, 
        p.peso_bruto, 
        p.preco, 
        p.familia as grupo,
        p.tipo,
        i.ipi, 
        i.iva_st, 
        i.icms 
    FROM t_cadastro_produto_v2 p
    LEFT JOIN t_imposto_v2 i ON i.produto_id = p.id
    WHERE p.status_produto = 'ATIVO'
""")
prods_db = pd.read_sql(sql_prods, conn)
# Normalize code for matching
prods_db['codigo_supra'] = prods_db['codigo_supra'].astype(str).str.strip()

# Pre-fetch Clients
print("Carregando clientes...")
sql_cli = text("""
    SELECT 
        cadastro_codigo_da_empresa as codigo_cliente, 
        cadastro_nome_cliente as nome_cliente,
        cadastro_ramo_de_atividade as ramo_de_atividade,
        ultimas_compras_cliente_calcula_st as calcula_st_flag
    FROM t_cadastro_cliente_v2
""")
cli_db = pd.read_sql(sql_cli, conn)
# Ensure string and strip
cli_db['codigo_cliente'] = cli_db['codigo_cliente'].astype(str).str.strip()

# Drop duplicates (keep first?)
cli_db = cli_db.drop_duplicates(subset=['codigo_cliente'])

# Convert to Dicts for fast lookup
prod_map = prods_db.set_index('codigo_supra').to_dict('index')
cli_map = cli_db.set_index('codigo_cliente').to_dict('index')

# Pre-fetch Payment Conditions
print("Carregando condições de pagamento...")
sql_cond = text("SELECT codigo_prazo, custo as taxa FROM t_condicoes_pagamento WHERE ativo IS TRUE")
cond_db = pd.read_sql(sql_cond, conn)
# Map: codigo -> taxa (decimal)
# Normalize keys to string for safer lookup
cond_db['codigo_prazo'] = cond_db['codigo_prazo'].astype(str).str.strip()
cond_map = cond_db.set_index('codigo_prazo')['taxa'].to_dict()

# Process Rows
print("Processando linhas com lógica refinada v3...")
output_rows = []

for idx, row in df_input.iterrows():
    # 1. Base Data
    cod_prod = str(row.get('codigo_produto_supra', '')).strip()
    cod_cli = str(row.get('codigo_cliente', '')).strip()
    
    # 2. Find Product
    prod_data = prod_map.get(cod_prod)
    
    # 3. Find Client & ST Logic
    cli_data = cli_map.get(cod_cli)
    calcula_st = False
    
    if cli_data:
        # Check explicit flag first
        flag = str(cli_data.get('calcula_st_flag', '')).upper()
        if flag in ['SIM', 'YES', 'TRUE', 'S', '1']:
            calcula_st = True
        elif flag in ['NAO', 'NO', 'FALSE', 'N', '0']:
            calcula_st = False
        else:
            # Fallback to Ramo
            ramo = str(cli_data.get('ramo_de_atividade', '')).upper()
            if 'REVENDA' in ramo or 'DISTRIBUIDORA' in ramo:
                calcula_st = True
    
    # 4. Fill / Calculate Fields
    
    # Product Basics
    desc = prod_data['nome_produto'] if prod_data else row.get('descricao_produto', '')
    emb = prod_data['embalagem_venda'] if prod_data else row.get('embalagem', '')
    peso_liq = safe_float(prod_data['peso']) if prod_data else safe_float(row.get('peso_liquido'))
    peso_bruto = safe_float(prod_data['peso_bruto']) if prod_data else peso_liq
    
    # Validations Logic
    peso_calc = peso_bruto if peso_bruto > 0 else peso_liq
    
    # Price
    preco_base = safe_float(prod_data['preco']) if prod_data else safe_float(row.get('valor_produto'))
    
    # Commercial
    comissao_val = safe_float(row.get('comissao_aplicada'))
    
    # Payment Condition
    cod_pagto_str = str(row.get('codigo_plano_pagamento', '')).strip()
    
    # Logic: Extract leading digits "123-Desc" -> "123"
    import re
    match = re.match(r'^(\d+)', cod_pagto_str)
    if match:
        cod_pagto_key = match.group(1)
    else:
        cod_pagto_key = cod_pagto_str
        
    taxa_cond = safe_float(cond_map.get(cod_pagto_key))
    
    # Ajuste Pagamento (Valor * Taxa)
    ajuste_val = preco_base * taxa_cond
    
    # Freight
    frete_kg = safe_float(row.get('frete_kg')) 
    valor_frete = (frete_kg / 1000.0) * peso_calc
    
    # Taxes
    tipo_prod = str(prod_data['tipo'] or '') if prod_data else ''
    is_pet = (tipo_prod.strip().lower() == 'pet')
    ipi_db = safe_float(prod_data['ipi']) if prod_data else 0.0
    
    ipi_rate = ipi_db if (is_pet and peso_liq <= 10) else 0.0
    
    # Base Calculation
    base_icms = preco_base + valor_frete + ajuste_val - comissao_val
    val_ipi = base_icms * ipi_rate
    
    # ST Logic
    val_st = 0.0
    iva_st_rate = safe_float(prod_data['iva_st']) if prod_data else 0.0
    
    if calcula_st and iva_st_rate > 0:
        val_st = base_icms * iva_st_rate

    # Markup
    markup = 0.0
    row_markup = row.get('markup')
    if row_markup: markup = safe_float(row_markup)
    
    
    # Totals
    valor_final = base_icms + val_ipi + val_st
    
    valor_final_markup = valor_final * (1 + markup/100.0)
    
    # Sem Frete
    base_sf = preco_base + ajuste_val - comissao_val
    val_ipi_sf = base_sf * ipi_rate
    val_st_sf = base_sf * iva_st_rate if (calcula_st and iva_st_rate > 0) else 0.0
    
    valor_sem_frete = base_sf + val_ipi_sf + val_st_sf
    
    # Construct New Row
    new_row = {
        'id_linha': idx + 1,
        'id_tabela': 0, 
        'nome_tabela': row.get('nome_tabela', ''),
        'fornecedor': row.get('fornecedor', 'Votorantim'),
        'codigo_cliente': cod_cli,
        'cliente': cli_data['nome_cliente'] if cli_data else row.get('cliente', ''),
        'codigo_produto_supra': cod_prod,
        'descricao_produto': desc,
        'embalagem': emb,
        'peso_liquido': round(peso_liq, 3),
        'valor_produto': round(preco_base, 2),
        'comissao_aplicada': round(comissao_val, 4),
        'ajuste_pagamento': round(ajuste_val, 2),
        'descricao_fator_comissao': row.get('descricao_fator_comissao', ''),
        'codigo_plano_pagamento': cod_pagto_str, # Keep original string or key? Original usually
        'markup': markup,
        'valor_final_markup': round(valor_final_markup, 2),
        'valor_s_frete_markup': round(valor_sem_frete * (1 + markup/100.0), 2),
        'valor_frete_aplicado': round(valor_frete, 2),
        'frete_kg': round(frete_kg, 3),
        'valor_frete': round(valor_final, 2),
        'valor_s_frete': round(valor_sem_frete, 2),
        'grupo': prod_data['grupo'] if prod_data else row.get('grupo', ''),
        'departamento': row.get('departamento', ''), 
        'ipi': round(val_ipi, 2),
        'icms_st': 0.0, 
        'iva_st': round(val_st, 2),
        'calcula_st': calcula_st,
        'ativo': True,
        'status_produto': 'ATIVO'
    }
    output_rows.append(new_row)

# Create Output DataFrame
df_out = pd.DataFrame(output_rows)

try:
    print(f"Salvando arquivo: {OUTPUT_FILE}")
    df_out.to_excel(OUTPUT_FILE, index=False)
    print("Concluído!")
except Exception as e:
    print(f"Erro ao salvar arquivo: {e}")

conn.close()
