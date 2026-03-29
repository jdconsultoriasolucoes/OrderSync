import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def check():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("--- Status Únicos em tb_pedidos ---")
        res = conn.execute(text("SELECT DISTINCT status FROM tb_pedidos")).fetchall()
        for r in res:
            print(f"'{r[0]}'")
            
        print("\n--- Exemplo de carga e seus pedidos ---")
        # Pega uma carga que NÃO é histórico
        carga = conn.execute(text("SELECT id, nome_carga, is_historico FROM tb_cargas WHERE is_historico = FALSE LIMIT 1")).fetchone()
        if carga:
            print(f"Carga ID: {carga.id}, Nome: {carga.nome_carga}, IsHist: {carga.is_historico}")
            pedidos = conn.execute(text("""
                SELECT cp.numero_pedido, p.status 
                FROM tb_cargas_pedidos cp
                LEFT JOIN tb_pedidos p ON p.id_pedido::text = cp.numero_pedido
                WHERE cp.id_carga = :cid
            """), {"cid": carga.id}).fetchall()
            for p in pedidos:
                print(f"  Pedido: {p.numero_pedido}, Status: {p.status}")
        else:
            print("Nenhuma carga ativa encontrada.")

if __name__ == "__main__":
    check()
