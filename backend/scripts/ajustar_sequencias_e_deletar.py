import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require'

def executar_ajustes():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Obter o ID máximo de pedido e item das tabelas de staging (carregados agora)
        cur.execute("SELECT COALESCE(max(id_pedido), 0) FROM tb_pedidos_ingestao;")
        max_pedido_ing = cur.fetchone()[0]
        
        cur.execute("SELECT COALESCE(max(id_item), 0) FROM tb_pedidos_itens_ingestao;")
        max_item_ing = cur.fetchone()[0]
        
        print(f"Último pedido carregado na ingestão: ID {max_pedido_ing}")
        print(f"Último item carregado na ingestão: ID {max_item_ing}")
        
        # 2. Deletar pedidos de produção com data anterior a 01/06/2026
        # Usamos 2026-06-01 00:00:00-03 para corresponder ao fuso local do usuário
        data_corte = '2026-06-01 00:00:00-03'
        
        print(f"Deletando itens de pedidos de produção com data anterior a {data_corte}...")
        cur.execute("""
            DELETE FROM tb_pedidos_itens 
            WHERE id_pedido IN (
                SELECT id_pedido 
                FROM tb_pedidos 
                WHERE created_at < %s::timestamptz OR criado_em < %s::timestamptz
            );
        """, (data_corte, data_corte))
        deleted_itens = cur.rowcount
        
        print(f"Deletando pedidos de produção com data anterior a {data_corte}...")
        cur.execute("""
            DELETE FROM tb_pedidos 
            WHERE created_at < %s::timestamptz OR criado_em < %s::timestamptz;
        """, (data_corte, data_corte))
        deleted_pedidos = cur.rowcount
        
        print(f"Deletados de produção: {deleted_pedidos} pedidos e {deleted_itens} itens.")
        
        # 3. Ajustar as sequências de autoincremento para iniciar a partir do último carregado
        if max_pedido_ing > 0:
            print(f"Ajustando sequência 'tb_pedidos_id_pedido_seq' para iniciar a partir de {max_pedido_ing}...")
            cur.execute("SELECT setval('tb_pedidos_id_pedido_seq', %s);", (max_pedido_ing,))
            
        if max_item_ing > 0:
            print(f"Ajustando sequência 'tb_pedidos_itens_id_item_seq' para iniciar a partir de {max_item_ing}...")
            cur.execute("SELECT setval('tb_pedidos_itens_id_item_seq', %s);", (max_item_ing,))
            
        conn.commit()
        print("\nAJUSTES EXECUTADOS COM SUCESSO NO BANCO DE DADOS!")
        
    except Exception as e:
        print(f"Erro: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == '__main__':
    executar_ajustes()
