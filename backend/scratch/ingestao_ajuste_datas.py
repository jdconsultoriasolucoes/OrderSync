import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
FILE_PATH = r'E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\ajuste_datas_pedidos.csv'

def ingestao_rapida():
    print(f"Lendo arquivo para ingestão: {FILE_PATH}")
    if not os.path.exists(FILE_PATH):
        print("Erro: Arquivo não encontrado.")
        return

    # Lendo o CSV
    df = pd.read_csv(FILE_PATH, sep=';', encoding='utf-8-sig')
    
    # Garantir que nota_fiscal seja string para evitar problemas de tipo
    df['nota_fiscal'] = df['nota_fiscal'].astype(str)

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        print("Preparando tabela tb_ajuste_datas_temp...")
        # Criar tabela temporária de suporte
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_ajuste_datas_temp (
                pedido_supra TEXT,
                nota_fiscal TEXT,
                confirmado_em TIMESTAMP,
                created_at TIMESTAMP
            );
            TRUNCATE TABLE tb_ajuste_datas_temp;
        """)

        # Preparar dados para inserção
        colunas = ['pedido_supra', 'nota_fiscal', 'confirmado_em', 'created_at']
        query = f"INSERT INTO tb_ajuste_datas_temp ({','.join(colunas)}) VALUES (%s, %s, %s, %s)"
        dados = [tuple(x) for x in df[colunas].values]

        print(f"Iniciando inserção de {len(dados)} registros...")
        execute_batch(cur, query, dados, page_size=1000)

        conn.commit()
        print("Ingestão concluída com sucesso na tabela tb_ajuste_datas_temp!")

    except Exception as e:
        print(f"Erro durante a ingestão: {e}")
        if 'conn' in locals(): conn.rollback()
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    ingestao_rapida()
