import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def check():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("--- Verificando Duplicatas em tb_background_tasks ---")
    cursor.execute("SELECT id, COUNT(*) FROM tb_background_tasks GROUP BY id HAVING COUNT(*) > 1;")
    dups = cursor.fetchall()
    
    if dups:
        print(f"ATENÇÃO: Encontrados {len(dups)} IDs duplicados!")
        for row in dups:
            print(f"ID {row[0]} aparece {row[1]} vezes.")
            
        print("Limpando duplicatas (mantendo apenas a mais recente)...")
        # Deleta duplicatas mantendo a com maior task_id ou criado_em
        cursor.execute("""
            DELETE FROM tb_background_tasks a
            USING tb_background_tasks b
            WHERE a.id = b.id AND a.ctid < b.ctid;
        """)
        print("Limpeza concluída.")
    else:
        print("Nenhum ID duplicado encontrado por chave primária.")

    print("\n--- Verificando Restrição de Unicidade em task_id ---")
    try:
        cursor.execute("ALTER TABLE tb_background_tasks ADD CONSTRAINT unique_task_id UNIQUE (task_id);")
        print("Constraint UNIQUE adicionada ao task_id.")
    except Exception as e:
        print(f"Nota: {e}")

    print("\n--- Limpando Tarefas Travadas (PENDENTE/PROCESSANDO antigas) ---")
    cursor.execute("DELETE FROM tb_background_tasks WHERE status IN ('PENDENTE', 'PROCESSANDO');")
    print("Tarefas pendentes limpas para reiniciar o worker do zero.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check()
