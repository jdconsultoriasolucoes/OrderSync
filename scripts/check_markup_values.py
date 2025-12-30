import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import text
from backend.database import SessionLocal

def check_last_tables():
    with SessionLocal() as db:
        print("Checking last 5 updated items...")
        sql = text("""
            SELECT id_tabela, id_linha, descricao_produto, valor_produto, 
                   markup, valor_final_markup, valor_s_frete_markup, editado_em
            FROM tb_tabela_preco
            ORDER BY editado_em DESC
            LIMIT 5
        """)
        rows = db.execute(sql).fetchall()
        for r in rows:
            print(f"ID: {r.id_tabela} | Prod: {r.descricao_produto} | Markup: {r.markup} | ValFinalMk: {r.valor_final_markup}")

if __name__ == "__main__":
    check_last_tables()
