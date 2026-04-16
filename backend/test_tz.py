from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DATABASE_URL)

def test_date_types():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT MAX(created_at) FROM tb_pedidos")).fetchone()
        val = res[0]
        now = datetime.now()
        
        print(f"Tipo do MAX(created_at): {type(val)}")
        print(f"Valor: {val}")
        print(f"TZ Info: {val.tzinfo if hasattr(val, 'tzinfo') else 'N/A'}")
        print(f"Tipo do datetime.now(): {type(now)}")
        
        try:
            is_less = val < now
            print(f"Comparação direta (val < now): {is_less}")
        except TypeError as e:
            print(f"ERRO DE COMPARAÇÃO: {e}")

if __name__ == "__main__":
    test_date_types()
