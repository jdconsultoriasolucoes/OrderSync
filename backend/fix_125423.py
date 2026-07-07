import os
from sqlalchemy import text
from database import SessionLocal

def run_fix():
    db = SessionLocal()
    try:
        # Pega todas as tabelas e pedidos que têm o código da Julia (125423) mas o nome não é Julia
        sql_tabela = text("""
            UPDATE tb_tabela_preco
            SET codigo_cliente = 'Não cadastrado'
            WHERE codigo_cliente = '125423'
              AND cliente NOT ILIKE '%JULIA PACHECO%'
        """)
        
        sql_pedido = text("""
            UPDATE tb_pedidos
            SET codigo_cliente = 'Não cadastrado'
            WHERE codigo_cliente = '125423'
              AND cliente NOT ILIKE '%JULIA PACHECO%'
        """)

        res_tabela = db.execute(sql_tabela)
        res_pedido = db.execute(sql_pedido)
        
        db.commit()
        
        print(f"Tabelas limpas do código da Julia: {res_tabela.rowcount}")
        print(f"Pedidos limpos do código da Julia: {res_pedido.rowcount}")

    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    run_fix()
