import os
# Hardcoded for debugging purposes
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from sqlalchemy import text

def debug_product():
    db = SessionLocal()
    with open("debug_res.txt", "w", encoding="utf-8") as f:
        try:
            # 1. Check Product Registration
            f.write("--- PULLING FROM t_cadastro_produto_v2 ---\n")
            # Use LIKE to catch it even if whitespace exists
            row = db.execute(
                text("SELECT id, codigo_supra, nome_produto, status_produto, tipo, fornecedor FROM t_cadastro_produto_v2 WHERE codigo_supra LIKE '%735F10%'")
            ).mappings().first()
            
            if row:
                f.write(f"Status: {row['status_produto']}\n")
                f.write(f"Codigo Supra Raw: '{row['codigo_supra']}'\n")
                f.write(f"Length: {len(row['codigo_supra'])}\n")
                tipo_prod = row['tipo']
                forn_prod = row['fornecedor']
            else:
                f.write("Produto 735F10 não encontrado na t_cadastro_produto_v2.\n")
                tipo_prod = None
                forn_prod = None

            # 2. Check PDF Ingestion Table
            f.write("\n--- PULLING FROM t_preco_produto_pdf_v2 (LAST 5 RECORDS) ---\n")
            rows_pdf = db.execute(
                text("""
                    SELECT codigo, lista, fornecedor, ativo, data_ingestao, preco_sc, nome_arquivo 
                    FROM t_preco_produto_pdf_v2 
                    WHERE codigo LIKE '%735F10%' 
                    ORDER BY data_ingestao DESC, id DESC 
                    LIMIT 5
                """)
            ).mappings().all()
            
            for r in rows_pdf:
                f.write(str(dict(r)) + "\n")
                # Also print length of 'codigo'
                f.write(f"Codigo PDF Raw: '{r['codigo']}', Length: {len(r['codigo'])}\n")

            if tipo_prod:
                # 3. Check Active List for this product's type/supplier
                f.write(f"\n--- CHECKING ACTIVE LIST FOR Tipo='{tipo_prod}' Fornecedor='{forn_prod}' ---\n")
                
                # Verifies if there is ANY active record for this group
                active_group = db.execute(text("""
                    SELECT COUNT(*) as qtd 
                    FROM t_preco_produto_pdf_v2 
                    WHERE ativo = TRUE AND lista = :l AND fornecedor = :f
                """), {"l": tipo_prod, "f": forn_prod}).scalar()
                
                f.write(f"Total active items for {tipo_prod}/{forn_prod}: {active_group}\n")
                
                # Check if THIS code is among them (EXACT MATCH)
                is_active_in_pdf = db.execute(text("""
                    SELECT COUNT(*) 
                    FROM t_preco_produto_pdf_v2 
                    WHERE ativo = TRUE AND lista = :l AND fornecedor = :f AND codigo = :c
                """), {"l": tipo_prod, "f": forn_prod, "c": row['codigo_supra']}).scalar()
                
                f.write(f"Is '{row['codigo_supra']}' in that active list (Exact Match)? {'YES' if is_active_in_pdf > 0 else 'NO'}\n")
                
        finally:
            db.close()

if __name__ == "__main__":
    debug_product()
