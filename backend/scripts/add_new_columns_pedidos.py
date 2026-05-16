import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def add_columns():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    tables = ['tb_pedidos', 'tb_pedidos_ingestao']
    
    for table in tables:
        print(f"Adicionando colunas em {table}...")
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS pedido_supra VARCHAR(100);")
            cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS nota_fiscal VARCHAR(100);")
            conn.commit()
            print(f"Colunas adicionadas com sucesso em {table}.")
        except Exception as e:
            conn.rollback()
            print(f"Erro ao alterar {table}: {e}")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    add_columns()
