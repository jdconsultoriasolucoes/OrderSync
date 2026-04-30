import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def check_schema():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    print("--- Inspecionando colunas de tb_tabela_preco ---")
    cursor.execute("""
        SELECT column_name, data_type, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_name = 'tb_tabela_preco'
        AND data_type = 'numeric';
    """)
    
    rows = cursor.fetchall()
    for row in rows:
        print(f"Coluna: {row[0]} | Tipo: {row[1]} | Precisão: {row[2]} | Escala: {row[3]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_schema()
