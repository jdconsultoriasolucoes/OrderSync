import os
from sqlalchemy import text
from database import SessionLocal

def check():
    db = SessionLocal()
    try:
        sql = text("""
            SELECT cadastro_codigo_da_empresa, cadastro_cnpj, cadastro_nome_cliente 
            FROM t_cadastro_cliente_v2 
            WHERE cadastro_nome_cliente ILIKE '%LUCAS P. CORDEIRO%'
               OR cadastro_cnpj ILIKE '%32.250.981%'
               OR cadastro_cnpj ILIKE '%32250981%'
        """)
        res = db.execute(sql).fetchall()
        print("LUCAS P. CORDEIRO:", res)
        
        sql2 = text("""
            SELECT cadastro_codigo_da_empresa, cadastro_cnpj, cadastro_nome_cliente 
            FROM t_cadastro_cliente_v2 
            WHERE cadastro_nome_cliente ILIKE '%TACIA ROSA FRANZINI%'
        """)
        res2 = db.execute(sql2).fetchall()
        print("TACIA ROSA FRANZINI:", res2)

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    check()
