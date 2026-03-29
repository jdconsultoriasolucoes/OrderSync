import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def check():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("--- Cargas com pedidos quase todos faturados ---")
        # Busca cargas que não são histórico
        cargas = conn.execute(text("SELECT id, numero_carga FROM tb_cargas WHERE is_historico = FALSE OR is_historico IS NULL")).fetchall()
        
        for c in cargas:
            pedidos = conn.execute(text("""
                SELECT cp.numero_pedido, p.status 
                FROM tb_cargas_pedidos cp
                LEFT JOIN tb_pedidos p ON p.id_pedido::text = cp.numero_pedido
                WHERE cp.id_carga = :cid
            """), {"cid": c.id}).fetchall()
            
            non_faturados = [p for p in pedidos if (p.status or "").lower() not in ('faturado supra', 'faturado dispet', 'cancelado')]
            
            if len(non_faturados) == 0 and len(pedidos) > 0:
                print(f"ERRO ENCONTRADO: Carga {c.id} (Nº {c.numero_carga}) deveria ser histórico mas não é!")
                for p in pedidos:
                    print(f"  Pedido {p.numero_pedido}: {p.status}")
            elif len(non_faturados) < 3 and len(pedidos) > 0:
                print(f"Carga {c.id} (Nº {c.numero_carga}) - {len(non_faturados)} pendentes:")
                for p in non_faturados:
                    print(f"  Pendente: {p.numero_pedido} -> {p.status}")

if __name__ == "__main__":
    check()
