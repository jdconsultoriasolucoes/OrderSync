import sqlalchemy
from sqlalchemy import create_engine, text

# URL de conexão oficial do banco PostgreSQL no Render
db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

def rodar_correcao():
    print("Iniciando script de correção histórica de códigos de clientes...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # 1. Atualizar pedidos órfãos
            print("Atualizando tb_pedidos...")
            res_pedidos = conn.execute(text("""
                UPDATE tb_pedidos p
                SET codigo_cliente = c.cadastro_codigo_da_empresa
                FROM t_cadastro_cliente_v2 c
                WHERE (p.codigo_cliente IS NULL OR p.codigo_cliente = '' OR LOWER(TRIM(p.codigo_cliente)) IN ('não cadastrado', 'nao cadastrado'))
                  AND LOWER(TRIM(p.cliente)) = LOWER(TRIM(c.cadastro_nome_cliente))
                  AND c.cadastro_codigo_da_empresa IS NOT NULL 
                  AND c.cadastro_codigo_da_empresa != ''
            """))
            print(f"Pedidos atualizados com sucesso: {res_pedidos.rowcount}")
            
            # 2. Atualizar tabelas de preços órfãs
            print("Atualizando tb_tabela_preco...")
            res_tabelas = conn.execute(text("""
                UPDATE tb_tabela_preco t
                SET codigo_cliente = c.cadastro_codigo_da_empresa
                FROM t_cadastro_cliente_v2 c
                WHERE (t.codigo_cliente IS NULL OR t.codigo_cliente = '' OR LOWER(TRIM(t.codigo_cliente)) IN ('não cadastrado', 'nao cadastrado'))
                  AND LOWER(TRIM(t.cliente)) = LOWER(TRIM(c.cadastro_nome_cliente))
                  AND c.cadastro_codigo_da_empresa IS NOT NULL 
                  AND c.cadastro_codigo_da_empresa != ''
            """))
            print(f"Tabelas de preços atualizadas com sucesso: {res_tabelas.rowcount}")
            
            conn.commit()
            print("Transação confirmada no banco de dados do Render.")
            
    except Exception as e:
        print(f"Erro ao executar a correção no banco: {e}")

if __name__ == "__main__":
    rodar_correcao()
