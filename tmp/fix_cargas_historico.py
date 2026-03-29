import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def fix_cargas():
    engine = create_engine(DATABASE_URL)
    fixed_count = 0
    with engine.begin() as conn:
        # Busca cargas que não são histórico
        cargas = conn.execute(text("SELECT id, numero_carga FROM tb_cargas WHERE is_historico = FALSE OR is_historico IS NULL")).fetchall()
        
        for c in cargas:
            pedidos = conn.execute(text("""
                SELECT cp.numero_pedido, p.status 
                FROM tb_cargas_pedidos cp
                LEFT JOIN tb_pedidos p ON TRIM(p.id_pedido::text) = TRIM(cp.numero_pedido)
                WHERE cp.id_carga = :cid
            """), {"cid": c.id}).fetchall()
            
            # Se não tem pedidos, ignorar por precaução, ou... mantemos original
            if len(pedidos) == 0:
                continue

            non_faturados = [p for p in pedidos if (p.status or "").lower().strip() not in ('faturado supra', 'faturado dispet', 'cancelado')]
            
            if len(non_faturados) == 0 and len(pedidos) > 0:
                print(f"Corrigindo Carga {c.id} (Nº {c.numero_carga}) - Todos os {len(pedidos)} pedidos estão com status final.")
                conn.execute(text("""
                    UPDATE tb_cargas
                    SET is_historico = TRUE,
                        data_faturamento = now(),
                        faturado_por_id = NULL
                    WHERE id = :carga_id
                """), {"carga_id": c.id})
                fixed_count += 1
                
        print(f"\nFinal concluído. Total de cargas movidas para histórico: {fixed_count}")

if __name__ == "__main__":
    fix_cargas()
