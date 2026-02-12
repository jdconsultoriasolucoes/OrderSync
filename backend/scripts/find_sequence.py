from sqlalchemy import create_engine, text

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DB_URL)

with engine.connect() as conn:
    # Try to find sequences associated with the table
    query = text("""
        SELECT c.relname FROM pg_class c 
        JOIN pg_depend d ON d.objid = c.oid 
        JOIN pg_class t ON d.refobjid = t.oid 
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
        WHERE t.relname = 'tb_tabela_preco' AND a.attname = 'id_linha' AND c.relkind = 'S';
    """)
    result = conn.execute(query)
    for row in result:
        print(f"Found sequence: {row[0]}")
    
    # Also try pg_get_serial_sequence
    query2 = text("SELECT pg_get_serial_sequence('tb_tabela_preco', 'id_linha');")
    result2 = conn.execute(query2)
    for row in result2:
        print(f"pg_get_serial_sequence: {row[0]}")
