import psycopg2

def run():
    print("Connecting to production DB...")
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()
    
    tables = [
        "tb_cargas_pedidos",
        "tb_cargas",
        "tb_retiradas_pedidos",
        "tb_retiradas"
    ]
    
    tables_str = ", ".join(tables)
    print(f"Truncating {tables_str}...")
    
    try:
        cur.execute(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE")
        conn.commit()
        print("Successfully truncated all logistics tables and reset IDs.")
    except Exception as e:
        conn.rollback()
        print(f"Error truncating tables: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run()
