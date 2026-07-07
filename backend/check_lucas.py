import os
from sqlalchemy import text
from database import SessionLocal

def run():
    db = SessionLocal()
    try:
        sql = text("SELECT cadastro_codigo_da_empresa, cadastro_cnpj, cadastro_nome_cliente, cadastro_nome_fantasia FROM t_cadastro_cliente_v2 WHERE cadastro_cnpj LIKE '%32250981%' OR cadastro_nome_cliente LIKE '%LUCAS%'")
        rows = db.execute(sql).fetchall()
        for r in rows:
            print("Row:", r)
    finally:
        db.close()

if __name__ == '__main__':
    run()
