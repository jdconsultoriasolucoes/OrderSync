import psycopg2
import sys
import os

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
CSV_PEDIDOS = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados\tb_pedidos_ingestao.csv"
CSV_ITENS = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\Ingestao\Processados\tb_pedidos_itens_ingestao.csv"

def run():
    print("Iniciando processo de ingestão...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        # 1. Deletar Itens Recentes (baseado na data do pedido)
        print("Deletando itens de pedidos a partir de 01/06/2026...")
        cur.execute("""
            DELETE FROM tb_pedidos_itens 
            WHERE id_pedido IN (
                SELECT id_pedido FROM tb_pedidos WHERE created_at >= '2026-06-01'
            )
        """)
        itens_deleted = cur.rowcount
        print(f"{itens_deleted} itens deletados.")
        
        # 2. Deletar Pedidos Recentes
        print("Deletando pedidos a partir de 01/06/2026...")
        cur.execute("DELETE FROM tb_pedidos WHERE created_at >= '2026-06-01'")
        pedidos_deleted = cur.rowcount
        print(f"{pedidos_deleted} pedidos deletados.")
        
        # 3. Carregar Pedidos via COPY
        print(f"Carregando {CSV_PEDIDOS}...")
        with open(CSV_PEDIDOS, 'r', encoding='utf-8-sig') as f:
            copy_sql = """
            COPY tb_pedidos (
                id_pedido, codigo_cliente, cliente, contato_nome, contato_email, contato_fone,
                tabela_preco_id, validade_ate, validade_dias, data_retirada, usar_valor_com_frete,
                itens, peso_total_kg, frete_total, total_sem_frete, total_com_frete, total_pedido,
                observacoes, status, confirmado_em, cancelado_em, cancelado_motivo, link_token,
                link_url, link_enviado_em, link_expira_em, link_primeiro_acesso_em, link_ultimo_acesso_em,
                link_qtd_acessos, link_status, criado_em, atualizado_em, created_at, fornecedor,
                tabela_preco_nome, atualizado_por, valor_frete_to, pedido_supra, nota_fiscal
            ) FROM STDIN WITH CSV HEADER DELIMITER ';' NULL ''
            """
            cur.copy_expert(copy_sql, f)
        print("Pedidos carregados com sucesso.")
        
        # 4. Carregar Itens via COPY
        print(f"Carregando {CSV_ITENS}...")
        with open(CSV_ITENS, 'r', encoding='utf-8-sig') as f:
            copy_sql_itens = """
            COPY tb_pedidos_itens (
                id_item, id_pedido, codigo, nome, embalagem, peso_kg, preco_unit,
                preco_unit_frt, quantidade, subtotal_sem_f, subtotal_com_f, condicao_pagamento, tabela_comissao, valor_frete_to
            ) FROM STDIN WITH CSV HEADER DELIMITER ';' NULL ''
            """
            cur.copy_expert(copy_sql_itens, f)
        print("Itens carregados com sucesso.")
        
        # 5. Atualizar Sequenciais
        print("Atualizando sequenciais (id_pedido e id_item)...")
        cur.execute("SELECT setval(pg_get_serial_sequence('tb_pedidos', 'id_pedido'), coalesce(max(id_pedido), 1)) FROM tb_pedidos")
        cur.execute("SELECT setval(pg_get_serial_sequence('tb_pedidos_itens', 'id_item'), coalesce(max(id_item), 1)) FROM tb_pedidos_itens")
        
        # Commit Final
        conn.commit()
        print("PROCESSO FINALIZADO E COMITADO!")
        
    except Exception as e:
        conn.rollback()
        print(f"ERRO: A transação foi revertida. Detalhes: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run()
