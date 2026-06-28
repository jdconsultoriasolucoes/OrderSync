import psycopg2
import re

def clean_cnpj(text):
    if not text: return ""
    return re.sub(r'\D', '', text)

def get_db():
    return psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')

def run():
    print("Connecting...")
    conn = get_db()
    cur = conn.cursor()

    print("Fetching active tables with invalid codigo_cliente...")
    cur.execute('''
        SELECT DISTINCT cliente, codigo_cliente
        FROM tb_tabela_preco 
        WHERE ativo = True 
          AND (
            codigo_cliente IS NULL 
            OR codigo_cliente = '' 
            OR codigo_cliente ILIKE '%não cadastr%'
            OR codigo_cliente ILIKE '%nao cadastr%'
            OR codigo_cliente ILIKE 'none'
          )
    ''')
    clientes = cur.fetchall()
    print(f"Found {len(clientes)} unique client names missing codes.")
    
    if not clientes:
        print("Nothing to update.")
        return

    print("Fetching all clients from t_cadastro_cliente_v2...")
    cur.execute('''
        SELECT cadastro_codigo_da_empresa, cadastro_cnpj, cadastro_nome_cliente, cadastro_nome_fantasia
        FROM t_cadastro_cliente_v2
    ''')
    db_clients = cur.fetchall()
    print(f"Loaded {len(db_clients)} registered clients.")
    
    updates = []
    
    for row in clientes:
        cli = row[0]
        match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', cli)
        if not match:
            # Also support digits without punctuation if they are 14 digits
            match = re.search(r'(\d{14})', cli)

        found_code = None
        
        if match:
            cnpj_clean = clean_cnpj(match.group(1))
            for r in db_clients:
                if clean_cnpj(r[1]) == cnpj_clean:
                    found_code = r[0]
                    break
        
        if not found_code:
            name_part = cli
            if match:
                name_part = cli.replace(match.group(1), '').strip(' -')
            name_part = re.sub(r'^\d+\s*-\s*', '', name_part).lower().strip()
            
            # Additional cleanups
            name_part = name_part.replace('ltda', '').replace('..', '').strip()
            
            for r in db_clients:
                n1 = (r[2] or "").lower()
                n2 = (r[3] or "").lower()
                if name_part and len(name_part) > 5 and (name_part in n1 or name_part in n2 or n1 in name_part or n2 in name_part):
                    found_code = r[0]
                    break
                    
        if found_code:
            updates.append((str(found_code), cli))

    print(f"Matched {len(updates)} clients. Updating DB...")
    
    from psycopg2.extras import execute_values
    
    cur.execute("CREATE TEMP TABLE tmp_update_cliente (codigo_cliente text, cliente text)")
    execute_values(cur, "INSERT INTO tmp_update_cliente (codigo_cliente, cliente) VALUES %s", updates)
    
    cur.execute('''
        UPDATE tb_tabela_preco t
        SET codigo_cliente = u.codigo_cliente
        FROM tmp_update_cliente u
        WHERE t.cliente = u.cliente 
          AND (
            t.codigo_cliente IS NULL 
            OR t.codigo_cliente = '' 
            OR t.codigo_cliente ILIKE '%não cadastr%'
            OR t.codigo_cliente ILIKE '%nao cadastr%'
            OR t.codigo_cliente ILIKE 'none'
          )
          AND t.ativo = True
    ''')
    
    updated_rows = cur.rowcount
    conn.commit()
    print(f"Successfully updated {updated_rows} rows in tb_tabela_preco.")

if __name__ == '__main__':
    run()
