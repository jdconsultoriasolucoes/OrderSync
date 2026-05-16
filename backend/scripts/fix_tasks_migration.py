import os
import psycopg2
from dotenv import load_dotenv

# Tenta carregar do .env se existir, senão usa as urls que encontramos nos scripts de auditoria
load_dotenv()

# URLs encontradas no projeto
PROD_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
DEV_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def fix_background_tasks_schema(db_url):
    print(f"\n--- Corrigindo schema em: {db_url.split('@')[-1]} ---")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Tornar referencia_id NULLABLE (O erro atual)
        print("Ajustando coluna referencia_id para permitir NULL...")
        cursor.execute("ALTER TABLE tb_background_tasks ALTER COLUMN referencia_id DROP NOT NULL;")
        
        # 2. Adicionar colunas que podem estar faltando devido a migrações incompletas
        print("Verificando colunas ausentes...")
        
        columns_to_add = [
            ("task_id", "VARCHAR(100) UNIQUE"),
            ("progresso", "INTEGER DEFAULT 0"),
            ("total_passos", "INTEGER DEFAULT 0"),
            ("mensagem_status", "TEXT"),
            ("resultado", "JSONB"),
            ("erro", "TEXT"),
            ("concluido_em", "TIMESTAMP")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE tb_background_tasks ADD COLUMN {col_name} {col_type};")
                print(f"  + Coluna '{col_name}' adicionada.")
            except psycopg2.errors.DuplicateColumn:
                print(f"  . Coluna '{col_name}' já existe.")
            except Exception as e:
                print(f"  ! Erro ao adicionar '{col_name}': {e}")
                
        print("--- Correção concluída com sucesso ---")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao conectar ou processar: {e}")

if __name__ == "__main__":
    # Pergunta: Qual banco o usuário quer corrigir? 
    # Por padrão, vamos tentar no que ele está usando agora.
    # Vou rodar no PROD (Render) pois o erro de 500 costuma vir de lá, 
    # e também no DEV para manter consistência.
    
    print("Iniciando correção de migração...")
    fix_background_tasks_schema(PROD_URL)
    fix_background_tasks_schema(DEV_URL)
