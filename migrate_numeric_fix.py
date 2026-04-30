import psycopg2

DB_URL = "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo"

def migrate():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    columns_to_fix = [
        "comissao_aplicada",
        "valor_frete_aplicado",
        "ipi",
        "icms_st",
        "iva_st",
        "markup",
        "frete_kg"
    ]
    
    print("--- Iniciando migração de precisão numérica ---")
    
    for col in columns_to_fix:
        print(f"Alterando coluna {col} para NUMERIC(18, 4)...")
        try:
            cursor.execute(f"ALTER TABLE tb_tabela_preco ALTER COLUMN {col} TYPE NUMERIC(18, 4);")
        except Exception as e:
            print(f"Erro ao alterar {col}: {e}")
            
    print("--- Migração concluída com sucesso ---")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate()
