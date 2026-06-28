import psycopg2
import re

def get_db():
    return psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')

def run():
    print("Connecting...")
    conn = get_db()
    cur = conn.cursor()

    # Find unmapped ones including 'não cadastrado'
    cur.execute('''
        SELECT DISTINCT cliente, codigo_cliente
        FROM tb_tabela_preco 
        WHERE ativo = True 
          AND (
            codigo_cliente IS NULL 
            OR codigo_cliente = '' 
            OR codigo_cliente ILIKE '%não cadastr%'
            OR codigo_cliente ILIKE '%nao cadastr%'
          )
    ''')
    clientes_missing = cur.fetchall()
    print(f"Found {len(clientes_missing)} unique client names/codes missing.")
    
    for c in clientes_missing[:20]:
        print(f"  - {c[0]} (Code currently: '{c[1]}')")

if __name__ == '__main__':
    run()
