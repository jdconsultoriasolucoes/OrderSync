import sys
from sqlalchemy import create_engine, inspect

DATABASE_URL = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

def check_specifics():
    try:
        engine = create_engine(DATABASE_URL)
        insp = inspect(engine)
        
        print("\n--- tb_tabela_preco ---")
        cols_tp = {c['name']: c for c in insp.get_columns("tb_tabela_preco")}
        
        # Check codigo_cliente type
        if 'codigo_cliente' in cols_tp:
            print(f"codigo_cliente: {cols_tp['codigo_cliente']['type']}")
        else:
            print("codigo_cliente: MISSING")
            
        # Check ramo_juridico existence
        print(f"ramo_juridico exists: {'ramo_juridico' in cols_tp}")
        
        # Check calcula_st existence
        print(f"calcula_st exists: {'calcula_st' in cols_tp}")

        print("\n--- t_cadastro_cliente ---")
        cols_cc = {c['name']: c for c in insp.get_columns("t_cadastro_cliente")}
        print(f"ramo_juridico exists: {'ramo_juridico' in cols_cc}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_specifics()
