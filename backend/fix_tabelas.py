import psycopg2
import re

def clean_cnpj(text):
    if not text: return ""
    return re.sub(r'\D', '', text)

def get_db():
    return psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')

def run():
    conn = get_db()
    cur = conn.cursor()

    print("Fetching active tables with missing codigo_cliente...")
    # Update only missing lines
    cur.execute('''
        SELECT DISTINCT cliente 
        FROM tb_tabela_preco 
        WHERE ativo = True 
          AND (codigo_cliente IS NULL OR codigo_cliente = '')
    ''')
    clientes = [r[0] for r in cur.fetchall()]
    
    print(f"Found {len(clientes)} unique client names.")
    
    update_count = 0
    not_found = []

    for cli in clientes:
        # try to extract CNPJ: nn.nnn.nnn/nnnn-nn
        match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', cli)
        found_code = None
        
        if match:
            cnpj_str = match.group(1)
            cnpj_clean = clean_cnpj(cnpj_str)
            cur.execute('''
                SELECT cadastro_codigo_da_empresa 
                FROM t_cadastro_cliente_v2 
                WHERE regexp_replace(cadastro_cnpj, '\\D', '', 'g') = %s
                LIMIT 1
            ''', (cnpj_clean,))
            res = cur.fetchone()
            if res:
                found_code = res[0]
        
        if not found_code:
            # try by name part
            name_part = cli
            if match:
                name_part = cli.replace(match.group(1), '').strip(' -')
            
            # remove some leading ids if formatted as "123 - Name"
            name_part = re.sub(r'^\d+\s*-\s*', '', name_part)
            
            cur.execute('''
                SELECT cadastro_codigo_da_empresa 
                FROM t_cadastro_cliente_v2 
                WHERE cadastro_nome_cliente ILIKE %s OR cadastro_nome_fantasia ILIKE %s
                LIMIT 1
            ''', (f'%{name_part}%', f'%{name_part}%'))
            res = cur.fetchone()
            if res:
                found_code = res[0]
                
        if found_code:
            cur.execute('''
                UPDATE tb_tabela_preco 
                SET codigo_cliente = %s 
                WHERE cliente = %s AND (codigo_cliente IS NULL OR codigo_cliente = '')
            ''', (str(found_code), cli))
            update_count += 1
        else:
            not_found.append(cli)
            
    conn.commit()
    print(f"Successfully mapped and updated {update_count} unique clients.")
    if not_found:
        print(f"Could not find mapping for {len(not_found)} clients:")
        for nf in not_found[:10]:
            print(f" - {nf}")
        if len(not_found) > 10:
            print(" ...")

if __name__ == '__main__':
    run()
