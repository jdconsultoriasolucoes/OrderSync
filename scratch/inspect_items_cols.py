import psycopg2

PROD_DB = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

def check():
    conn = psycopg2.connect(PROD_DB)
    cursor = conn.cursor()
    
    print("--- Colunas de tb_pedidos_itens ---")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tb_pedidos_itens'
        ORDER BY column_name;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"Col: {row[0]} | Type: {row[1]}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check()
