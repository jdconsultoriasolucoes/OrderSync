
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add backend to path to find any necessary modules if needed, though we just need env
sys.path.append(os.path.join(os.getcwd(), 'backend'))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment.")
    sys.exit(1)

# Fix for Render/Postgres if needed (sslmode)
if "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

def run_migrations():
    print(f"Connecting to DB...")
    engine = create_engine(DATABASE_URL)

    statements = [
        # 1. Tabela Usuario
        """
        ALTER TABLE t_usuario 
        ADD COLUMN IF NOT EXISTS criado_por VARCHAR;
        """,
        
        # 2. Clientes V2
        """
        ALTER TABLE t_cadastro_cliente_v2 
        ADD COLUMN IF NOT EXISTS criado_por VARCHAR,
        ADD COLUMN IF NOT EXISTS atualizado_por VARCHAR;
        """,

        # 3. Produtos V2
        """
        ALTER TABLE t_cadastro_produto_v2 
        ADD COLUMN IF NOT EXISTS criado_por VARCHAR,
        ADD COLUMN IF NOT EXISTS atualizado_por VARCHAR;
        """,

        # 4. Pedido Link
        """
        ALTER TABLE tb_pedido_link 
        ADD COLUMN IF NOT EXISTS criado_por VARCHAR;
        """,

        # 5. Config Email SMTP
        """
        ALTER TABLE config_email_smtp 
        ADD COLUMN IF NOT EXISTS atualizado_por VARCHAR;
        """,
        
        # 6. Config Email Mensagem (Subject/Body configs if table exists)
        """
        CREATE TABLE IF NOT EXISTS config_email_mensagem (id SERIAL PRIMARY KEY); -- Ensure exists slightly
        ALTER TABLE config_email_mensagem 
        ADD COLUMN IF NOT EXISTS atualizado_por VARCHAR;
        """
    ]

    with engine.connect() as conn:
        for stmt in statements:
            try:
                # Cleaning up potential whitespace/comments for cleaner logs
                clean_stmt = stmt.strip()
                if "CREATE TABLE IF NOT EXISTS config_email_mensagem" in clean_stmt:
                     # config_email_mensagem might already exist with columns, just ensuring for the ALTER below
                     pass
                
                print(f"Executing: {clean_stmt.splitlines()[1].strip()} ...")
                conn.execute(text(clean_stmt))
                print("  -> Success")
            except Exception as e:
                print(f"  -> Error (might be okay if table missing): {e}")
        
        conn.commit()
    
    print("\nMigration checks completed.")

if __name__ == "__main__":
    run_migrations()
