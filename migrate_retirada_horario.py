import psycopg2
import sys

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

def main():
    print("Iniciando migração no Render PostgreSQL...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Adiciona a coluna retirada_horario se não existir
        print("Adicionando coluna 'retirada_horario' à tabela 'tb_cargas_pedidos'...")
        cur.execute("""
            ALTER TABLE public.tb_cargas_pedidos 
            ADD COLUMN IF NOT EXISTS retirada_horario VARCHAR;
        """)
        
        # Adiciona a coluna observacoes se não existir (garantia)
        print("Adicionando coluna 'observacoes' à tabela 'tb_cargas_pedidos'...")
        cur.execute("""
            ALTER TABLE public.tb_cargas_pedidos 
            ADD COLUMN IF NOT EXISTS observacoes VARCHAR;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
