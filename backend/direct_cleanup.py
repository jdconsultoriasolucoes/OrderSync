import os
import psycopg2

# Config database handling
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ordersync_db")

def run():
    try:
        print("Connecting via psycopg2...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            options="-c client_encoding=latin1"
        )
        
        # Force encoding again just to be sure
        conn.set_client_encoding('LATIN1')
        print("Connected and Encoding set to LATIN1.")
        
        cur = conn.cursor()
        
        sql = """
        SELECT COUNT(*) FROM (
            SELECT 
                id, 
                row_number() OVER (
                    PARTITION BY codigo_supra, tipo 
                    ORDER BY 
                        CASE WHEN fornecedor ILIKE '%VOTORANTIM%' THEN 1 ELSE 2 END ASC,
                        id DESC
                ) as rn
            FROM public.t_cadastro_produto_v2
            WHERE status_produto = 'ATIVO'
        ) t
        WHERE t.rn > 1;
        """
        
        cur.execute(sql)
        count = cur.fetchone()[0]
        print(f"DUPLICATES TO DELETE: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {repr(e)}")

if __name__ == "__main__":
    run()
