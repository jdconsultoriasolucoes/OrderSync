import sys
import os
sys.path.append('backend')
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from sqlalchemy import text
from database import SessionLocal

def check_duplication(pedido_id):
    sql = text("""
        SELECT
            i.codigo              AS item_codigo,
            i.nome                AS item_nome,
            i.quantidade          AS item_quantidade,
            
            tp.id_linha           AS tp_id_linha,
            tp.codigo_produto_supra AS tp_codigo,
            tp.ativo              AS tp_ativo,
            
            prod.codigo_supra     AS prod_codigo,
            prod.status_produto   AS prod_status,
            prod.id               AS prod_id

        FROM tb_pedidos p
        
        JOIN tb_pedidos_itens i
            ON i.id_pedido = p.id_pedido
            
        -- Join suspeito 1: Tabela de Preço
        LEFT JOIN tb_tabela_preco tp
            ON tp.id_tabela = p.tabela_preco_id 
            AND tp.codigo_produto_supra = i.codigo
            AND tp.ativo = TRUE

        -- Join suspeito 2: Cadastro de Produto
        LEFT JOIN t_cadastro_produto_v2 prod
            ON prod.codigo_supra = i.codigo
            AND prod.fornecedor = tp.fornecedor

        WHERE p.id_pedido = :pid
        ORDER BY i.codigo;
    """)

    with SessionLocal() as db:
        rows = db.execute(sql, {"pid": pedido_id}).mappings().all()
        
        print(f"--- Diagnostico Pedido {pedido_id} ---")
        print(f"Total de linhas retornadas (raw): {len(rows)}")
        
        counts = {}
        for r in rows:
            cod = r['item_codigo']
            counts[cod] = counts.get(cod, 0) + 1
            
        duplicates = {k:v for k,v in counts.items() if v > 1}
        
        if not duplicates:
            print("Nenhuma duplicidade encontrada na query RAW.")
        else:
            print(f"ITENS DUPLICADOS: {list(duplicates.keys())}")
            for cod in duplicates:
                print(f"\nDetalhes para {cod}:")
                subset = [r for r in rows if r['item_codigo'] == cod]
                for s in subset:
                    print(f"  -> Qtd: {s['item_quantidade']} | TP_ID: {s['tp_id_linha']} (Ativo: {s['tp_ativo']}) | PROD_ID: {s['prod_id']} (Status: {s['prod_status']})")

if __name__ == "__main__":
    check_duplication(304)
