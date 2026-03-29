import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def dry_run_check(id_pedido):
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print(f"--- Debandando Cargas para Pedido {id_pedido} ---")
        cargas = conn.execute(text("""
            SELECT DISTINCT c.id, c.is_historico 
            FROM tb_cargas c
            JOIN tb_cargas_pedidos cp ON cp.id_carga = c.id
            WHERE cp.numero_pedido = :id_pedido AND (c.is_historico IS NULL OR c.is_historico = FALSE)
        """), {"id_pedido": str(id_pedido)}).fetchall()
        
        print(f"Cargas encontradas: {[r[0] for r in cargas]}")
        
        for carga_row in cargas:
            carga_id = carga_row[0]
            print(f"\nAnalisando Carga {carga_id}...")
            
            # Detalhes dos pedidos da carga
            detalhes = conn.execute(text("""
                SELECT cp.numero_pedido, p.status, LOWER(p.status) as lower_status
                FROM tb_cargas_pedidos cp
                LEFT JOIN tb_pedidos p ON p.id_pedido::text = cp.numero_pedido
                WHERE cp.id_carga = :carga_id
            """), {"carga_id": carga_id}).fetchall()
            
            for d in detalhes:
                is_terminal = (d.lower_status or "") in ('faturado supra', 'faturado dispet', 'cancelado')
                print(f"  Pedido {d.numero_pedido}: Status='{d.status}', Terminal={is_terminal}")
            
            total_pendente = conn.execute(text("""
                SELECT COUNT(*) as total_pendente
                FROM tb_cargas_pedidos cp
                JOIN tb_pedidos p ON p.id_pedido::text = cp.numero_pedido
                WHERE cp.id_carga = :carga_id
                  AND LOWER(p.status) NOT IN ('faturado supra', 'faturado dispet', 'cancelado')
            """), {"carga_id": carga_id}).scalar()
            
            print(f"Total Pendente (conforme query original): {total_pendente}")
            
            if total_pendente == 0:
                print(">> CONDICAO SATISFEITA: is_historico seria TRUE")
            else:
                print(">> CONDICAO NAO SATISFEITA")

if __name__ == "__main__":
    dry_run_check(581) # Carga 39
    print("-" * 20)
    dry_run_check(507) # Carga 44
