import os
from sqlalchemy import text
from database import engine

def reset_tables():
    dialect = engine.dialect.name
    tables = [
        "tb_cargas_pedidos",
        "tb_cargas",
        "tb_retiradas_pedidos",
        "tb_retiradas"
    ]
    
    with engine.begin() as conn:
        if dialect == 'sqlite':
            for table in tables:
                conn.execute(text(f"DELETE FROM {table}"))
                try:
                    conn.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table}'"))
                except Exception:
                    pass
        elif dialect == 'postgresql':
            # Reverse order for foreign key constraints if dropping individually, 
            # but cascade handles it, although doing it in one command is safer
            tables_str = ", ".join(tables)
            conn.execute(text(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE"))
        else:
            for table in tables:
                conn.execute(text(f"DELETE FROM {table}"))

if __name__ == "__main__":
    reset_tables()
    print("Logistics tables reset successfully.")
