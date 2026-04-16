from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DATABASE_URL)

def list_columns():
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'tb_pedidos'
        """)).all()
        for r in res:
            print(f"{r[0]}: {r[1]}")

if __name__ == "__main__":
    list_columns()
