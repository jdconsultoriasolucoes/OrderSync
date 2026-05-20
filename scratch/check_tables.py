import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require"

def check_tables():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # Listar colunas de tb_pedidos
    print("--- Colunas de tb_pedidos ---")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tb_pedidos'
        ORDER BY ordinal_position;
    """)
    for row in cursor.fetchall():
        print(f"{row[0]} ({row[1]})")
        
    # Listar colunas de tb_pedidos_importados
    print("\n--- Colunas de tb_pedidos_importados ---")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tb_pedidos_importados'
        ORDER BY ordinal_position;
    """)
    for row in cursor.fetchall():
        print(f"{row[0]} ({row[1]})")
        
    # Listar outras tabelas no esquema public
    print("\n--- Outras tabelas em public ---")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    for row in cursor.fetchall():
        print(row[0])
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_tables()
