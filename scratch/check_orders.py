import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def check_orders():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT count(*) FROM tb_pedidos;")
        count = cur.fetchone()[0]
        print(f"Total de pedidos em tb_pedidos: {count}")
        
        if count > 0:
            cur.execute("SELECT min(criado_em), max(criado_em), min(created_at), max(created_at) FROM tb_pedidos;")
            min_criado, max_criado, min_created, max_created = cur.fetchone()
            print(f"criado_em: min={min_criado}, max={max_criado}")
            print(f"created_at: min={min_created}, max={max_created}")
            
            cur.execute("SELECT id_pedido, criado_em, created_at FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 5;")
            print("Últimos 5 pedidos:")
            for r in cur.fetchall():
                print(r)
        
        cur.execute("SELECT count(*) FROM tb_pedidos_ingestao;")
        count_ing = cur.fetchone()[0]
        print(f"Total de pedidos em tb_pedidos_ingestao: {count_ing}")
        
        if count_ing > 0:
            cur.execute("SELECT max(id_pedido) FROM tb_pedidos_ingestao;")
            max_id_ing = cur.fetchone()[0]
            print(f"ID máximo em tb_pedidos_ingestao: {max_id_ing}")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    check_orders()
