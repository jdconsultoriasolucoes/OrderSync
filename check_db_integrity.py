import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def fix():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("1. Removendo duplicatas físicas...")
    cursor.execute("""
        DELETE FROM tb_background_tasks a
        USING tb_background_tasks b
        WHERE a.id = b.id AND a.ctid < b.ctid;
    """)
    
    print("2. Resetando a sequência de IDs...")
    try:
        # Tenta descobrir o nome da sequência ou usa o padrão do Postgres para SERIAL
        cursor.execute("SELECT pg_get_serial_sequence('tb_background_tasks', 'id');")
        seq_name = cursor.fetchone()[0]
        if seq_name:
            cursor.execute(f"SELECT setval('{seq_name}', (SELECT MAX(id) FROM tb_background_tasks));")
            print(f"Sequência {seq_name} sincronizada com o valor máximo.")
    except Exception as e:
        print(f"Erro ao sincronizar sequência: {e}")

    print("3. Limpando tarefas pendentes para reiniciar...")
    cursor.execute("DELETE FROM tb_background_tasks WHERE status IN ('PENDENTE', 'PROCESSANDO');")
    
    print("--- Operação concluída com sucesso ---")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    fix()
