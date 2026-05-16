import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def migrate():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    commands = [
        "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS progresso INTEGER DEFAULT 0;",
        "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS total_passos INTEGER DEFAULT 0;",
        "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS mensagem_status TEXT;"
    ]
    
    for cmd in commands:
        try:
            print(f"Executando: {cmd}")
            cursor.execute(cmd)
            print("OK")
        except Exception as e:
            print(f"Erro: {e}")

    cursor.close()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    migrate()
