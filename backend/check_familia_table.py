import psycopg2

# URL Provided by user
DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def run():
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(dsn=DATABASE_URL)
        cur = conn.cursor()
        
        print("Checking for t_familia_produtos...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE  table_schema = 'public'
                AND    table_name   = 't_familia_produtos'
            );
        """)
        exists = cur.fetchone()[0]
        print(f"Table Exists: {exists}")
        
        if exists:
             print("Table Columns:")
             cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_familia_produtos';")
             for row in cur.fetchall():
                 print(row)
                 
             print("\nTable Content (Limit 10):")
             cur.execute("SELECT * FROM public.t_familia_produtos LIMIT 10")
             for row in cur.fetchall():
                 print(row)

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
