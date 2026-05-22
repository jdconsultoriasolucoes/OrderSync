from sqlalchemy import create_engine, inspect

db_urls = [
    "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo",
    "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"
]

for url in db_urls:
    print(f"\n=====================================")
    print(f"Testing URL: {url.split('@')[1]}")
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Connection successful! Tables: {len(tables)}")
        
        if 'tb_pedidos' in tables:
            columns = inspector.get_columns('tb_pedidos')
            print("Columns in tb_pedidos:")
            for col in columns:
                if 'st' in col['name'].lower() or 'iva' in col['name'].lower() or 'frete' in col['name'].lower():
                    print(f"  - {col['name']} ({col['type']})")
                    
        if 'tb_pedidos_itens' in tables:
            columns = inspector.get_columns('tb_pedidos_itens')
            print("Columns in tb_pedidos_itens:")
            for col in columns:
                if 'st' in col['name'].lower() or 'iva' in col['name'].lower() or 'frete' in col['name'].lower():
                    print(f"  - {col['name']} ({col['type']})")
    except Exception as e:
        print(f"Error: {e}")
