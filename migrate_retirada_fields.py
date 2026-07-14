import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.begin() as conn:
        print("Adicionando colunas de controle de retirada na tabela tb_cargas...")
        
        # Adiciona is_retirada se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas 
            ADD COLUMN IF NOT EXISTS is_retirada BOOLEAN DEFAULT FALSE;
        """))
        
        # Adiciona tipo_retirada se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas 
            ADD COLUMN IF NOT EXISTS tipo_retirada VARCHAR(50) NULL;
        """))
        
        # Adiciona retirada_nome_terceiro se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas 
            ADD COLUMN IF NOT EXISTS retirada_nome_terceiro VARCHAR(255) NULL;
        """))

        # Adiciona retirada_veiculo_temporario_placa se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas 
            ADD COLUMN IF NOT EXISTS retirada_veiculo_temporario_placa VARCHAR(20) NULL;
        """))

        # Adiciona retirada_veiculo_temporario_modelo se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas 
            ADD COLUMN IF NOT EXISTS retirada_veiculo_temporario_modelo VARCHAR(100) NULL;
        """))

    print("Colunas de retirada adicionadas à tabela tb_cargas com sucesso.")
except Exception as e:
    print(f"Erro ao executar migracao: {e}")
