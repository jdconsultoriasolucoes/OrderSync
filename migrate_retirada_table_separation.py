from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

sql_statements = [
    # 1. Tabela tb_retiradas
    """
    CREATE TABLE IF NOT EXISTS tb_retiradas (
        id SERIAL PRIMARY KEY,
        nome_retirada VARCHAR(255) NULL,
        numero_retirada VARCHAR(100) UNIQUE NULL,
        data_retirada TIMESTAMP NULL,
        is_historico BOOLEAN DEFAULT FALSE,
        data_criacao TIMESTAMP DEFAULT NOW(),
        data_update TIMESTAMP DEFAULT NOW()
    );
    """,
    # 2. Tabela tb_retiradas_pedidos
    """
    CREATE TABLE IF NOT EXISTS tb_retiradas_pedidos (
        id SERIAL PRIMARY KEY,
        id_retirada INTEGER REFERENCES tb_retiradas(id) ON DELETE CASCADE,
        numero_pedido VARCHAR(100) NULL,
        observacoes TEXT NULL,
        retirada_tipo VARCHAR(50) NULL,
        retirada_nome_terceiro VARCHAR(255) NULL,
        retirada_veiculo_modelo VARCHAR(255) NULL,
        retirada_veiculo_placa VARCHAR(50) NULL,
        retirada_horario VARCHAR(50) NULL
    );
    """,
    # Índices para performance
    "CREATE INDEX IF NOT EXISTS idx_tb_retiradas_numero ON tb_retiradas(numero_retirada);",
    "CREATE INDEX IF NOT EXISTS idx_tb_retiradas_pedidos_id_ret ON tb_retiradas_pedidos(id_retirada);",
    "CREATE INDEX IF NOT EXISTS idx_tb_retiradas_pedidos_num_ped ON tb_retiradas_pedidos(numero_pedido);"
]

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Iniciando migração de tabelas separadas para retiradas...")
        for stmt in sql_statements:
            conn.execute(text(stmt))
            conn.commit()
        print("Migração concluída com sucesso!")
except Exception as e:
    print(f"Erro na migração: {e}")
