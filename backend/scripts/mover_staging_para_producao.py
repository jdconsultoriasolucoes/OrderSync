import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require'

import time

def connect_with_retry(db_url, max_retries=5, delay=2):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return psycopg2.connect(db_url)
        except psycopg2.OperationalError as e:
            last_error = e
            print(f"Tentativa de conexao {attempt}/{max_retries} falhou: {e}. Retentando em {delay}s...")
            time.sleep(delay)
    raise last_error

def move_to_production():
    conn = connect_with_retry(DB_URL)
    cur = conn.cursor()
    
    try:
        print("Movendo dados de Staging para Produção...")
        
        # 1. Mover Pedidos
        cur.execute("""
            INSERT INTO tb_pedidos (
                id_pedido, codigo_cliente, cliente, contato_nome, contato_email, contato_fone,
                tabela_preco_id, validade_ate, validade_dias, data_retirada, usar_valor_com_frete,
                itens, peso_total_kg, frete_total, total_sem_frete, total_com_frete, total_pedido,
                observacoes, status, confirmado_em, cancelado_em, cancelado_motivo, link_token,
                link_url, link_enviado_em, link_expira_em, link_primeiro_acesso_em, link_ultimo_acesso_em,
                link_qtd_acessos, link_status, criado_em, atualizado_em, created_at, fornecedor,
                tabela_preco_nome, atualizado_por, valor_frete_to, pedido_supra, nota_fiscal
            )
            SELECT 
                id_pedido, codigo_cliente, cliente, contato_nome, contato_email, contato_fone,
                tabela_preco_id, validade_ate, validade_dias, data_retirada, usar_valor_com_frete,
                itens::jsonb, peso_total_kg, frete_total, total_sem_frete, total_com_frete, total_pedido,
                observacoes, status, confirmado_em, cancelado_em, cancelado_motivo, link_token,
                link_url, link_enviado_em, link_expira_em, link_primeiro_acesso_em, link_ultimo_acesso_em,
                link_qtd_acessos, link_status, criado_em, atualizado_em, created_at, fornecedor,
                tabela_preco_nome, atualizado_por, valor_frete_to, pedido_supra, nota_fiscal
            FROM tb_pedidos_ingestao;
        """)
        
        # 2. Mover Itens
        cur.execute("""
            INSERT INTO tb_pedidos_itens (
                id_item, id_pedido, codigo, nome, embalagem, peso_kg, preco_unit,
                preco_unit_frt, quantidade, subtotal_sem_f, subtotal_com_f, condicao_pagamento, tabela_comissao, valor_frete_to
            )
            SELECT 
                id_item, id_pedido, codigo, nome, embalagem, peso_kg, preco_unit,
                preco_unit_frt, quantidade, subtotal_sem_f, subtotal_com_f, condicao_pagamento, tabela_comissao, valor_frete_to
            FROM tb_pedidos_itens_ingestao;
        """)
        
        # 3. Sincronizar Sequências
        cur.execute("SELECT setval('tb_pedidos_id_pedido_seq', (SELECT MAX(id_pedido) FROM tb_pedidos))")
        cur.execute("SELECT setval('tb_pedidos_itens_id_item_seq', (SELECT MAX(id_item) FROM tb_pedidos_itens))")
        
        conn.commit()
        print("Dados movidos para produção com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao mover dados: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    move_to_production()
