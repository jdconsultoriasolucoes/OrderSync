import psycopg2
from psycopg2 import sql

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def create_table():
    print("Conectando ao banco de dados no Render...")
    try:
        conn = psycopg2.connect(DB_URL + "?sslmode=require")
        cur = conn.cursor()
        
        # Cria a tabela de logs de erro
        cur.execute("""
            CREATE TABLE IF NOT EXISTS error_logs (
                id SERIAL PRIMARY KEY,
                modulo VARCHAR(255),
                status_code INTEGER,
                mensagem TEXT NOT NULL,
                payload JSONB,
                usuario_id INTEGER,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Cria índice para facilitar buscas por data ou módulo
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_logs_data ON error_logs(data_hora);
            CREATE INDEX IF NOT EXISTS idx_error_logs_modulo ON error_logs(modulo);
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Tabela 'error_logs' criada com sucesso no PostgreSQL.")
    except Exception as e:
        print(f"Erro ao conectar ou criar tabela: {e}")

if __name__ == "__main__":
    create_table()
