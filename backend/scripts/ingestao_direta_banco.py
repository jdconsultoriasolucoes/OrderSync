import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import math
import os

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
FILE_PEDIDOS = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados\tb_pedidos_ingestao.csv'
FILE_ITENS = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados\tb_pedidos_itens_ingestao.csv'

def clean_value(val):
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return None
    return val

def importar_para_staging():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Limpando profundamente o sistema (Pedidos, Itens, Links, Cargas e Históricos)...")
        # Tabelas de Ingestão (Staging)
        cur.execute("TRUNCATE TABLE tb_pedidos_itens_ingestao RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_pedidos_ingestao RESTART IDENTITY CASCADE;")
        
        # Tabelas de Produção (Limpeza Geral conforme solicitado)
        cur.execute("TRUNCATE TABLE tb_pedidos_itens RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_pedidos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_pedido_link RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_idempotency_keys RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_cliente_historico RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_cargas_pedidos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE tb_cargas RESTART IDENTITY CASCADE;")
        
        conn.commit()
        print("Sistema limpo e IDs zerados com sucesso!")
        
        # 1. tb_pedidos_ingestao
        print(f"Lendo dados de pedidos: {FILE_PEDIDOS}")
        if not os.path.exists(FILE_PEDIDOS):
            print(f"Erro: Arquivo {FILE_PEDIDOS} nao encontrado.")
            return
            
        df_p = pd.read_csv(FILE_PEDIDOS, sep=';', encoding='utf-8-sig')
        
        # Preenchimento de campos obrigatorios ou criticos
        df_p['peso_total_kg'] = df_p['peso_total_kg'].fillna(0)
        df_p['frete_total'] = df_p['frete_total'].fillna(0)
        df_p['total_com_frete'] = df_p['total_com_frete'].fillna(0)
        df_p['total_pedido'] = df_p['total_pedido'].fillna(0)
        df_p['tabela_preco_id'] = df_p['tabela_preco_id'].fillna(1)
        df_p['valor_frete_to'] = df_p['valor_frete_to'].fillna(0)
        
        # Limpar NaN para None (NULL no Postgres)
        df_p = df_p.map(clean_value)
        
        colunas_p = list(df_p.columns)
        insert_p = f"INSERT INTO tb_pedidos_ingestao ({','.join(colunas_p)}) VALUES ({','.join(['%s']*len(colunas_p))})"
        dados_p = [tuple(row) for row in df_p.itertuples(index=False, name=None)]
        
        print("Inserindo em tb_pedidos_ingestao...")
        execute_batch(cur, insert_p, dados_p, page_size=500)
        
        # 2. tb_pedidos_itens_ingestao
        print(f"Lendo dados de itens: {FILE_ITENS}")
        if not os.path.exists(FILE_ITENS):
            print(f"Erro: Arquivo {FILE_ITENS} nao encontrado.")
            return

        df_i = pd.read_csv(FILE_ITENS, sep=';', encoding='utf-8-sig')
        
        # Preenchimento de campos obrigatorios
        df_i['subtotal_sem_f'] = df_i['subtotal_sem_f'].fillna(0)
        df_i['preco_unit_frt'] = df_i['preco_unit_frt'].fillna(0)
        df_i['subtotal_com_f'] = df_i['subtotal_com_f'].fillna(0)
        df_i['peso_kg'] = df_i['peso_kg'].fillna(0)
        df_i['valor_frete_to'] = df_i['valor_frete_to'].fillna(0)
        
        # Limpar NaN para None
        df_i = df_i.map(clean_value)
        
        colunas_i = list(df_i.columns)
        insert_i = f"INSERT INTO tb_pedidos_itens_ingestao ({','.join(colunas_i)}) VALUES ({','.join(['%s']*len(colunas_i))})"
        dados_i = [tuple(row) for row in df_i.itertuples(index=False, name=None)]
        
        print("Inserindo em tb_pedidos_itens_ingestao...")
        execute_batch(cur, insert_i, dados_i, page_size=500)
        
        conn.commit()
        print("IMPORTACAO CONCLUIDA NAS TABELAS DE INGESTAO COM SUCESSO!")
        
    except Exception as e:
        print(f"Erro: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == '__main__':
    importar_para_staging()
