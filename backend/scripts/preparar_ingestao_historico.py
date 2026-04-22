import pandas as pd
import os
import json
from datetime import datetime

# Configurações de Caminho
INPUT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Tb_ingestao_historico_pedido.xlsx'
INCREMENT_FILE = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\tabelas_incremento.xlsx'
OUTPUT_DIR = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados'

def processar_historico():
    print(f"Lendo base original: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERRO: Arquivo não encontrado em {INPUT_FILE}")
        return

    if not os.path.exists(INCREMENT_FILE):
        print(f"ERRO: Arquivo de incrementos não encontrado em {INCREMENT_FILE}")
        return

    # 1. Carregar dados auxiliares
    print(f"Carregando tabelas de incremento: {INCREMENT_FILE}")
    df_cond = pd.read_excel(INCREMENT_FILE, sheet_name='condicao_pagamento')
    df_desc = pd.read_excel(INCREMENT_FILE, sheet_name='desconto')

    # Limpeza e normalização das chaves auxiliares
    df_cond.columns = [c.strip() for c in df_cond.columns]
    df_desc.columns = [c.strip() for c in df_desc.columns]

    # Mapeamentos (Dicionários para busca rápida)
    # condicao_pagamento: 'Condies Pagamento' -> 'custo'
    map_cond = df_cond.set_index('Condições Pagamento')['custo'].to_dict()
    
    # desconto: 'Lista' -> 'Desconto' (fator numérico) e Nome Formatado
    map_desc = df_desc.set_index('Lista')['Desconto'].to_dict()
    
    def format_comissao(row_desc):
        try:
            tabela_val = float(row_desc['Tabela'])
            tabela = str(int(tabela_val)) if tabela_val.is_integer() else str(tabela_val)
        except:
            tabela = str(row_desc['Tabela']).strip()
            
        # Converter 0.1414 para 14.14
        desc_perc = round(float(row_desc['Desconto']) * 100, 2)
        return f"{tabela} - {desc_perc}"
    
    map_comissao_nome = df_desc.set_index('Lista').apply(format_comissao, axis=1).to_dict()

    # 2. Carregar base de histórico
    df = pd.read_excel(INPUT_FILE)
    
    # 3. Aplicar Regras de Negócio e Cálculos Comerciais
    print("Aplicando descontos e condições de pagamento...")

    # Os preços já vêm calculados do Excel (conforme feedback do usuário)
    df['preco_final_unit'] = df['Preço Unitario']
    
    # Manter nomes das tabelas de comissão e condição apenas para fins de exibição/strings
    def get_desc_nome(row):
        lista_raw = str(row['Lista']).split('-')[0].strip()
        try:
            lista_key = int(lista_raw) if lista_raw.isdigit() else lista_raw
        except:
            lista_key = lista_raw
        return map_comissao_nome.get(lista_key, "0 - 0.0")

    df['comissao_nome'] = df.apply(get_desc_nome, axis=1)

    # Cálculos por linha
    df['subtotal_sem_f'] = df['Qtde'] * df['preco_final_unit']
    
    # Frete e outros campos de total serão tratados no banco, mantemos como referencia se necessário
    df['frete_unit_kg'] = df['Frete(TO)'] / 1000
    df['preco_unit_frt'] = df['preco_final_unit'] + df['frete_unit_kg']
    df['subtotal_com_f'] = df['Qtde'] * df['preco_unit_frt']
    
    # 2. Agrupamento e Mapeamento de IDs
    print("Consolidando pedidos e gerando IDs sequenciais...")
    
    pedidos_lista = []
    itens_lista = []
    
    map_pedido_id = {}
    next_pedido_id = 20000
    next_item_id = 200000
    
    grupos = df.groupby('Pedido')
    
    for num_pedido_original, group in grupos:
        primeira_linha = group.iloc[0]
        id_pedido_novo = next_pedido_id
        map_pedido_id[num_pedido_original] = id_pedido_novo
        next_pedido_id += 1
        
        # Calcular totais do pedido
        total_sem_frete = group['subtotal_sem_f'].sum()
        
        # Gerar JSON de itens para snapshot
        itens_json = []
        for _, row in group.iterrows():
            desc_cols = [c for c in row.index if 'Descri' in c]
            desc_val = row[desc_cols[0]] if desc_cols else ""
            
            # Gerar dicionário do item filtrando valores None para economizar espaço
            item_obj = {
                "codigo": str(row['Produto']).strip(),
                "descricao": str(desc_val)[:80], # Limitar descrição no snapshot
                "quantidade": row['Qtde'],
                "preco_unit": row['preco_final_unit'],
                "unidade": row['Unidade']
            }
            # Adicionar apenas se não for nulo (v2 optimization)
            if row['preco_unit_frt'] and not pd.isna(row['preco_unit_frt']):
                item_obj["preco_unit_com_frete"] = row['preco_unit_frt']
            
            itens_json.append(item_obj)
            
            # Lógica simplificada: preço final já inclui tudo
            tem_frete = row['Frete(TO)'] > 0
            sub_total = round(row['Qtde'] * row['preco_final_unit'], 2)
            
            itens_lista.append({
                "id_item": next_item_id,
                "id_pedido": id_pedido_novo,
                "codigo": str(row['Produto']).strip()[:80],
                "nome": desc_val,
                "embalagem": str(row['Unidade']).strip(),
                "peso_kg": None,
                "preco_unit": round(row['preco_final_unit'], 2),
                "preco_unit_frt": round(row['preco_final_unit'], 2),
                "quantidade": row['Qtde'],
                "subtotal_sem_f": 0 if tem_frete else sub_total,
                "subtotal_com_f": sub_total if tem_frete else 0,
                "condicao_pagamento": str(row['Cond. Pagto']).strip().replace('-', ' - ', 1),
                "tabela_comissao": row['comissao_nome'],
                "valor_frete_to": row['Frete(TO)']
            })
            next_item_id += 1
        
        # Adicionar à lista de pedidos (tb_pedidos)
        pedidos_lista.append({
            "id_pedido": id_pedido_novo,
            "codigo_cliente": str(primeira_linha['Codigo'])[:80],
            "cliente": str(primeira_linha['Cliente'])[:255],
            "contato_nome": "",
            "contato_email": "",
            "contato_fone": "",
            "tabela_preco_id": None,
            "validade_ate": None,
            "validade_dias": None,
            "data_retirada": None,
            "usar_valor_com_frete": True if primeira_linha['Frete(TO)'] > 0 else False,
            "itens": json.dumps(itens_json, ensure_ascii=False, separators=(',', ':')), # Compacto
            "peso_total_kg": None,
            "frete_total": primeira_linha['Frete(TO)'], # Mantendo como valor original por enquanto
            "total_sem_frete": 0 if primeira_linha['Frete(TO)'] > 0 else round(total_sem_frete, 2),
            "total_com_frete": round(total_sem_frete, 2) if primeira_linha['Frete(TO)'] > 0 else 0,
            "total_pedido": round(total_sem_frete, 2),
            "observacoes": "Importação Histórica",
            "status": "Orçamento",
            "confirmado_em": primeira_linha['Emissão'],
            "cancelado_em": None,
            "cancelado_motivo": None,
            "link_token": None,
            "link_url": None,
            "link_enviado_em": None,
            "link_expira_em": None,
            "link_primeiro_acesso_em": None,
            "link_ultimo_acesso_em": None,
            "link_qtd_acessos": 0,
            "link_status": "DESABILITADO",
            "criado_em": datetime.now(),
            "atualizado_em": datetime.now(),
            "created_at": primeira_linha['Emissão'],
            "fornecedor": primeira_linha['Local'],
            "tabela_preco_nome": "ingestão manual",
            "atualizado_por": "Admin",
            "valor_frete_to": primeira_linha['Frete(TO)']
        })

    # Criar DataFrames com ordem de colunas exata
    cols_pedidos = [
        "id_pedido", "codigo_cliente", "cliente", "contato_nome", "contato_email", "contato_fone",
        "tabela_preco_id", "validade_ate", "validade_dias", "data_retirada", "usar_valor_com_frete",
        "itens", "peso_total_kg", "frete_total", "total_sem_frete", "total_com_frete", "total_pedido",
        "observacoes", "status", "confirmado_em", "cancelado_em", "cancelado_motivo", "link_token",
        "link_url", "link_enviado_em", "link_expira_em", "link_primeiro_acesso_em", "link_ultimo_acesso_em",
        "link_qtd_acessos", "link_status", "criado_em", "atualizado_em", "created_at", "fornecedor",
        "tabela_preco_nome", "atualizado_por", "valor_frete_to"
    ]
    
    cols_itens = [
        "id_item", "id_pedido", "codigo", "nome", "embalagem", "peso_kg", "preco_unit",
        "preco_unit_frt", "quantidade", "subtotal_sem_f", "subtotal_com_f", "condicao_pagamento", "tabela_comissao", "valor_frete_to"
    ]
    
    df_pedidos_final = pd.DataFrame(pedidos_lista)[cols_pedidos]
    df_itens_final = pd.DataFrame(itens_lista)[cols_itens]
    
    # Garantir tipos numericos para o Excel
    numeric_pedidos = ["peso_total_kg", "frete_total", "total_sem_frete", "total_com_frete", "total_pedido", "valor_frete_to"]
    for col in numeric_pedidos:
        df_pedidos_final[col] = pd.to_numeric(df_pedidos_final[col], errors='coerce').fillna(0)
        
    numeric_itens = ["peso_kg", "preco_unit", "preco_unit_frt", "quantidade", "subtotal_sem_f", "subtotal_com_f", "valor_frete_to"]
    for col in numeric_itens:
        df_itens_final[col] = pd.to_numeric(df_itens_final[col], errors='coerce').fillna(0)

    # Criar pasta de saída se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Salvar resultados em ambos os formatos
    path_pedidos_csv = os.path.join(OUTPUT_DIR, 'tb_pedidos_ingestao.csv')
    path_itens_csv = os.path.join(OUTPUT_DIR, 'tb_pedidos_itens_ingestao.csv')
    path_pedidos_xlsx = os.path.join(OUTPUT_DIR, 'tb_pedidos_ingestao.xlsx')
    path_itens_xlsx = os.path.join(OUTPUT_DIR, 'tb_pedidos_itens_ingestao.xlsx')
    
    # CSV para o script de ingestão (padrao interno .)
    df_pedidos_final.to_csv(path_pedidos_csv, index=False, sep=';', encoding='utf-8-sig')
    df_itens_final.to_csv(path_itens_csv, index=False, sep=';', encoding='utf-8-sig')
    
    # XLSX para visualização humana (Excel reconhece numeros nativos)
    df_pedidos_final.to_excel(path_pedidos_xlsx, index=False)
    df_itens_final.to_excel(path_itens_xlsx, index=False)
    
    print("\nPROCESSO CONCLUÍDO COM SUCESSO!")
    print(f"-> Arquivos CSV (Ingestão): {path_pedidos_csv}")
    print(f"-> Arquivos XLSX (Visualização): {path_pedidos_xlsx}")
    print(f"Total de pedidos processados: {len(df_pedidos_final)}")
    
    max_json = df_pedidos_final['itens'].apply(len).max()
    print(f"Tamanho máximo da coluna 'itens': {max_json} caracteres")
    if max_json > 4096:
        print("AVISO: Alguns pedidos excedem 4096 caracteres. Certifique-se de que a coluna do banco é do tipo TEXT.")

if __name__ == "__main__":
    processar_historico()
