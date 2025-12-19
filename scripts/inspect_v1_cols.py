import sys
from sqlalchemy import create_engine, inspect

# URL fornecida pelo usuário
DATABASE_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def check_columns():
    try:
        engine = create_engine(DATABASE_URL)
        insp = inspect(engine)
        
        table = "t_cadastro_produto"
        if table in insp.get_table_names():
            print(f"\n--- Colunas de {table} ---")
            for col in insp.get_columns(table):
                print(f"- {col['name']} ({col['type']})")
        else:
            print(f"❌ Tabela {table} não encontrada.")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_columns()
