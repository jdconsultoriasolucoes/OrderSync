import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def inspect_tables():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    tables = ['tb_pedidos', 'tb_pedidos_ingestao']
    
    for table in tables:
        print(f"\n--- Colunas de {table} ---")
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position;
        """)
        for row in cur.fetchall():
            print(f"{row[0]}: {row[1]}")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_tables()
