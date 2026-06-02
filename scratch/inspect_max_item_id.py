import psycopg2

DB_URL = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'

def inspect_max_item_id():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        cur.execute("SELECT max(id_item) FROM tb_pedidos_itens_ingestao;")
        max_id = cur.fetchone()[0]
        print(f"ID de item máximo em tb_pedidos_itens_ingestao: {max_id}")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    inspect_max_item_id()
