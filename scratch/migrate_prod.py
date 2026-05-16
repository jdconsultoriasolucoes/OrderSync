import sqlalchemy as sa
from sqlalchemy import text

prod_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

commands = [
    # t_cadastro_cliente_v2
    "ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN IF NOT EXISTS elaboracao_local_carregamento TEXT;",
    
    # tb_background_tasks
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS progresso INTEGER;",
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS total_passos INTEGER;",
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS mensagem_status TEXT;",
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS task_id VARCHAR(255);",
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS resultado JSONB;",
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS erro TEXT;",
    "ALTER TABLE tb_background_tasks ADD COLUMN IF NOT EXISTS concluido_em TIMESTAMP;",
    
    # tb_pedidos
    "ALTER TABLE tb_pedidos ADD COLUMN IF NOT EXISTS frete_kg DOUBLE PRECISION;",
    
    # tb_pedidos_itens
    "ALTER TABLE tb_pedidos_itens ADD COLUMN IF NOT EXISTS manual_freight BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE tb_pedidos_itens ADD COLUMN IF NOT EXISTS valor_frete_unitario NUMERIC(14, 2);",
    "ALTER TABLE tb_pedidos_itens ADD COLUMN IF NOT EXISTS markup NUMERIC(18, 4) DEFAULT 0;",
    "ALTER TABLE tb_pedidos_itens ADD COLUMN IF NOT EXISTS valor_final_markup NUMERIC(14, 2) DEFAULT 0;",
    "ALTER TABLE tb_pedidos_itens ADD COLUMN IF NOT EXISTS valor_s_frete_markup NUMERIC(14, 2) DEFAULT 0;",
    "ALTER TABLE tb_pedidos_itens ADD COLUMN IF NOT EXISTS frete_base_ton DOUBLE PRECISION DEFAULT 0;",
    
    # tb_tabela_preco
    "ALTER TABLE tb_tabela_preco ADD COLUMN IF NOT EXISTS observacao VARCHAR(100);",
    "ALTER TABLE tb_tabela_preco ADD COLUMN IF NOT EXISTS manual_freight BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE tb_tabela_preco ADD COLUMN IF NOT EXISTS frete_base_ton DOUBLE PRECISION DEFAULT 0;"
]

def run_migration():
    engine = sa.create_engine(prod_url)
    with engine.connect() as conn:
        print("Iniciando migração em PRODUÇÃO...")
        for cmd in commands:
            try:
                print(f"Executando: {cmd}")
                conn.execute(text(cmd))
                conn.commit()
                print("Sucesso.")
            except Exception as e:
                print(f"Erro ao executar '{cmd}': {e}")
        print("\nMigração concluída.")

if __name__ == "__main__":
    run_migration()
