from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to hardcoded URL if env var not set (development convenience)
    DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Verificando se a coluna 'status_anterior' existe na tabela 't_cadastro_produto_v2'...")
        
        # Check column existence
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 't_cadastro_produto_v2' 
              AND column_name = 'status_anterior'
        """)).fetchone()

        if not result:
            print("Coluna nao encontrada. Adicionando 'status_anterior'...")
            conn.execute(text("ALTER TABLE public.t_cadastro_produto_v2 ADD COLUMN status_anterior TEXT"))
            conn.commit()
            print("Coluna 'status_anterior' adicionada com sucesso.")
        else:
            print("Coluna 'status_anterior' ja existe. Nenhuma alteracao necessaria.")

if __name__ == "__main__":
    migrate()
