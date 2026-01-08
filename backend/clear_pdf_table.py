import psycopg2

# URL Provided by user
DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def run():
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(dsn=DATABASE_URL)
        cur = conn.cursor()
        
        print("Truncating table public.t_preco_produto_pdf_v2...")
        cur.execute("TRUNCATE TABLE public.t_preco_produto_pdf_v2;")
        conn.commit()
        
        print("Success: Table t_preco_produto_pdf_v2 cleared.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
