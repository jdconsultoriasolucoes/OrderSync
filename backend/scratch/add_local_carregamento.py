import os
import psycopg2

DATABASE_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def migrate():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Adicionando coluna elaboracao_local_carregamento...")
        cur.execute("""
            ALTER TABLE t_cadastro_cliente_v2 
            ADD COLUMN IF NOT EXISTS elaboracao_local_carregamento TEXT;
        """)
        
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro na migração: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
