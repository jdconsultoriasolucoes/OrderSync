import os
import psycopg2

# Config database handling
# URL Provided by user
DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def run():
    try:
        print("Connecting via psycopg2...")
        conn = psycopg2.connect(
            dsn=DATABASE_URL,
            options="-c client_encoding=latin1"
        )
        
        conn.set_client_encoding('LATIN1')
        cur = conn.cursor()
        
        target_code = '1426E10.1'
        
        print(f"\nScanning for Code: {target_code}")
        
        # 1. Check Product Table
        print("\n--- t_cadastro_produto_v2 (Existing) ---")
        sql_prod = """
            SELECT 
                id,
                codigo_supra, encode(codigo_supra::bytea, 'hex'),
                tipo, encode(tipo::bytea, 'hex'),
                fornecedor, encode(fornecedor::bytea, 'hex')
            FROM public.t_cadastro_produto_v2
            WHERE codigo_supra LIKE '%1426E10.1%'
        """
        cur.execute(sql_prod)
        rows = cur.fetchall()
        for r in rows:
            print(f"Row ID: {r[0]}")
            print(f"  Code: '{r[1]}' (Hex: {r[2]})")
            print(f"  Tipo: '{r[3]}' (Hex: {r[4]})")
            print(f"  Forn: '{r[5]}' (Hex: {r[6]})")
            
        # 2. Check PDF Table
        print("\n--- t_preco_produto_pdf_v2 (Import Source) ---")
        sql_pdf = """
            SELECT 
                codigo, encode(codigo::bytea, 'hex'),
                lista, encode(lista::bytea, 'hex'),
                fornecedor, encode(fornecedor::bytea, 'hex')
            FROM public.t_preco_produto_pdf_v2
            WHERE codigo LIKE '%1426E10.1%' AND ativo=TRUE
        """
        cur.execute(sql_pdf)
        rows = cur.fetchall()
        for r in rows:
            print(f"PDF Row found:")
            print(f"  Code: '{r[0]}' (Hex: {r[1]})")
            print(f"  List: '{r[2]}' (Hex: {r[3]})")
            print(f"  Forn: '{r[4]}' (Hex: {r[5]})")

        conn.close()
        
    except Exception as e:
        print(f"Error: {repr(e)}")

if __name__ == "__main__":
    run()
