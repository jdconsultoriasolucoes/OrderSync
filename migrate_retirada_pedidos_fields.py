import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.begin() as conn:
        print("Adicionando colunas de controle de retirada na tabela tb_cargas_pedidos...")
        
        # Adiciona retirada_tipo se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas_pedidos 
            ADD COLUMN IF NOT EXISTS retirada_tipo VARCHAR(50) NULL;
        """))
        
        # Adiciona retirada_nome_terceiro se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas_pedidos 
            ADD COLUMN IF NOT EXISTS retirada_nome_terceiro VARCHAR(255) NULL;
        """))
        
        # Adiciona retirada_veiculo_modelo se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas_pedidos 
            ADD COLUMN IF NOT EXISTS retirada_veiculo_modelo VARCHAR(255) NULL;
        """))

        # Adiciona retirada_veiculo_placa se nao existir
        conn.execute(text("""
            ALTER TABLE public.tb_cargas_pedidos 
            ADD COLUMN IF NOT EXISTS retirada_veiculo_placa VARCHAR(50) NULL;
        """))

    print("Colunas de retirada adicionadas à tabela tb_cargas_pedidos com sucesso.")
except Exception as e:
    print(f"Erro ao executar migracao: {e}")
