import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os

# Configurações
file_path = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\base_clientes_2804.xlsx'
conn_str = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
target_table = 'tb_ingestao_clientes_2804'
source_template_table = 't_cadastro_cliente_v2'

try:
    print(f"Lendo Excel: {file_path}...")
    df_excel = pd.read_excel(file_path, header=1)
    
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    
    # Obtém o schema do banco
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{source_template_table}' ORDER BY ordinal_position")
    col_names = [row[0] for row in cur.fetchall() if row[0] != 'id']
    
    df_final = pd.DataFrame(columns=col_names)
    
    print("Mapeando campos com novos ajustes (Ramo Jurídico -> Tipo de Cliente)...")
    for index, row in df_excel.iterrows():
        new_row = {col: None for col in col_names}
        
        # Mapeamento por índice para segurança
        new_row['cadastro_codigo_da_empresa'] = str(row.iloc[0]).split('.')[0] if not pd.isna(row.iloc[0]) else None
        new_row['cadastro_nome_cliente'] = str(row.iloc[1])
        new_row['cadastro_nome_fantasia'] = str(row.iloc[2])
        new_row['tipo_pessoa'] = str(row.iloc[3])
        
        # AJUSTE SOLICITADO: Ramo Jurídico (Índice 4) -> Tipo de Cliente
        new_row['cadastro_tipo_cliente'] = str(row.iloc[4])
        new_row['cadastro_ramo_de_atividade'] = str(row.iloc[4]) # Mantemos no ramo também
        
        new_row['elaboracao_vendedor'] = str(row.iloc[5])
        new_row['compras_nome_responsavel'] = str(row.iloc[6])
        new_row['compras_telefone_fixo_responsavel'] = str(row.iloc[7])
        new_row['compras_email_resposavel'] = str(row.iloc[8])
        
        ativo_str = str(row.iloc[9]).upper()
        new_row['cadastro_ativo'] = True if 'SIM' in ativo_str or 'ATIVO' in ativo_str and 'NO' not in ativo_str else False
        
        # Endereço unificado
        end_completo = f"{row.iloc[12]}, {row.iloc[13]}".strip(', ')
        new_row['faturamento_endereco'] = end_completo
        new_row['entrega_endereco'] = end_completo
        new_row['faturamento_bairro'] = str(row.iloc[14])
        new_row['entrega_bairro'] = str(row.iloc[14])
        new_row['faturamento_cep'] = str(row.iloc[15])
        new_row['entrega_cep'] = str(row.iloc[15])
        new_row['faturamento_municipio'] = str(row.iloc[16])
        new_row['entrega_municipio'] = str(row.iloc[16])
        new_row['faturamento_estado'] = str(row.iloc[17])
        new_row['entrega_estado'] = str(row.iloc[17])
        
        doc = str(row.iloc[18])
        if len(doc.replace('.', '').replace('-', '').replace('/', '')) > 11:
            new_row['cadastro_cnpj'] = doc
        else:
            new_row['cadastro_cpf'] = doc
            
        new_row['cadastro_inscricao_estadual'] = str(row.iloc[19])
        new_row['cadastro_periodo_de_compra'] = str(row.iloc[30])
        
        new_row['ultimas_compras_valor_total'] = pd.to_numeric(row.iloc[25], errors='coerce')
        new_row['ultimas_compras_previsao_proxima'] = str(row.iloc[31])
        new_row['obs_nao_compra_observacoes'] = str(row.iloc[32])
        new_row['entrega_observacao_motorista'] = str(row.iloc[44])
        new_row['supervisor_nome_pet'] = str(row.iloc[50])
        
        df_final = pd.concat([df_final, pd.DataFrame([new_row])], ignore_index=True)

    # Limpeza de linhas vazias antes da carga
    df_final = df_final[df_final['cadastro_nome_cliente'].notna() & (df_final['cadastro_nome_cliente'] != 'nan')]

    print("Recriando tabela de ingestão e carregando dados...")
    cur.execute(f"DROP TABLE IF EXISTS {target_table}")
    cur.execute(f"CREATE TABLE {target_table} (LIKE {source_template_table} INCLUDING ALL)")
    try: cur.execute(f"ALTER TABLE {target_table} DROP COLUMN id")
    except: pass
    cur.execute(f"ALTER TABLE {target_table} ADD COLUMN id SERIAL PRIMARY KEY")

    cols_to_insert = [c for c in df_final.columns if c != 'id']
    placeholders = ", ".join(["%s"] * len(cols_to_insert))
    cols_str = ", ".join([f'"{c}"' for c in cols_to_insert])
    insert_query = f'INSERT INTO {target_table} ({cols_str}) VALUES ({placeholders})'
    
    data_to_insert = df_final[cols_to_insert].where(pd.notnull(df_final[cols_to_insert]), None).values.tolist()
    execute_batch(cur, insert_query, data_to_insert)
    
    conn.commit()
    print(f"Ingestão concluída! {len(df_final)} registros carregados.")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"Erro: {e}")
