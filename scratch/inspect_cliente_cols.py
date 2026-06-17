import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def check_schema():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    print("--- Colunas de t_cadastro_cliente_v2 ---")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 't_cadastro_cliente_v2'
        ORDER BY column_name;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"Col: {row[0]} | Type: {row[1]}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_schema()
