import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def create_staging_tables():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    print("Criando tabelas de staging se não existirem...")
    
    # Criar tb_pedidos_ingestao baseada em tb_pedidos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_pedidos_ingestao (
            id_pedido BIGSERIAL PRIMARY KEY,
            codigo_cliente VARCHAR(80),
            cliente VARCHAR(255),
            contato_nome VARCHAR(255),
            contato_email VARCHAR(255),
            contato_fone VARCHAR(255),
            tabela_preco_id INTEGER,
            validade_ate DATE,
            validade_dias INTEGER,
            data_retirada DATE,
            usar_valor_com_frete BOOLEAN,
            itens TEXT,
            peso_total_kg NUMERIC,
            frete_total NUMERIC,
            total_sem_frete NUMERIC,
            total_com_frete NUMERIC,
            total_pedido NUMERIC,
            observacoes VARCHAR(255),
            status VARCHAR(50),
            confirmado_em TIMESTAMP WITH TIME ZONE,
            cancelado_em TIMESTAMP WITH TIME ZONE,
            cancelado_motivo VARCHAR(255),
            link_token VARCHAR(255),
            link_url TEXT,
            link_enviado_em TIMESTAMP WITH TIME ZONE,
            link_expira_em TIMESTAMP WITH TIME ZONE,
            link_primeiro_acesso_em TIMESTAMP WITH TIME ZONE,
            link_ultimo_acesso_em TIMESTAMP WITH TIME ZONE,
            link_qtd_acessos INTEGER DEFAULT 0,
            link_status VARCHAR(50),
            criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE,
            fornecedor TEXT,
            tabela_preco_nome VARCHAR(255),
            atualizado_por VARCHAR(100),
            valor_frete_to NUMERIC,
            pedido_supra VARCHAR(100),
            nota_fiscal VARCHAR(100)
        );
    """)
    
    # Criar tb_pedidos_itens_ingestao baseada em tb_pedidos_itens
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_pedidos_itens_ingestao (
            id_item BIGSERIAL PRIMARY KEY,
            id_pedido BIGINT,
            codigo VARCHAR(80),
            nome TEXT,
            embalagem VARCHAR(50),
            peso_kg NUMERIC,
            preco_unit NUMERIC,
            preco_unit_frt NUMERIC,
            quantidade NUMERIC,
            subtotal_sem_f NUMERIC,
            subtotal_com_f NUMERIC,
            condicao_pagamento VARCHAR(100),
            tabela_comissao VARCHAR(100),
            valor_frete_to NUMERIC
        );
    """)
    
    conn.commit()
    print("Tabelas de staging criadas/verificadas com sucesso.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_staging_tables()
