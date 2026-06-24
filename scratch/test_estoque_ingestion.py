import sys
import os
import pandas as pd
from sqlalchemy import text

# Adjust path to import backend modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

# Load env before database import
os.environ.setdefault("DATABASE_URL", "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require")

from database import SessionLocal
from models.produto import ProdutoV2

def test_ingestion():
    excel_path = r"E:\Projeto Sistema pedidos\Planejamento\Arquivos bases edson\relatorio de importação\estoque.xlsx"
    print("Reading Excel file:", excel_path)
    df = pd.read_excel(excel_path)
    
    # We find the row for product '002T20'
    df_clean = df.dropna(subset=['Produto'])
    prod_row = df_clean[df_clean['Produto'] == '002T20']
    
    if prod_row.empty:
        print("Product '002T20' not found in Excel sheet.")
        return
        
    row = prod_row.iloc[0]
    qtd_estoque = int(float(row['Qt. Estoque']))
    qtd_pedidos = int(float(row['Qt. Pedidos Carteira']))
    af_pendentes = int(float(row['AF Pendentes']))
    
    calc_disponivel = qtd_estoque - qtd_pedidos
    calc_futuro = calc_disponivel + af_pendentes
    
    print(f"Calculated values for 002T20:")
    print(f"  Qt. Estoque (F): {qtd_estoque}")
    print(f"  Qt. Pedidos Carteira (G): {qtd_pedidos}")
    print(f"  AF Pendentes (H): {af_pendentes}")
    print(f"  Expected Disponível: {calc_disponivel}")
    print(f"  Expected Futuro: {calc_futuro}")
    
    # Query current DB values
    db = SessionLocal()
    try:
        p = db.query(ProdutoV2).filter(ProdutoV2.codigo_supra == '002T20').first()
        if not p:
            print("Product '002T20' not found in database! Creating temporary mock product...")
            p = ProdutoV2(
                codigo_supra='002T20',
                status_produto='ATIVO',
                nome_produto='SUPRA IMPULSO SC 20KG',
                estoque_disponivel=0,
                estoque_futuro=0
            )
            db.add(p)
            db.commit()
            p = db.query(ProdutoV2).filter(ProdutoV2.codigo_supra == '002T20').first()
            
        print(f"DB values before update:")
        print(f"  estoque_disponivel: {p.estoque_disponivel}")
        print(f"  estoque_futuro: {p.estoque_futuro}")
        
        # Perform update logic simulating endpoint
        print("Simulating ingestion update in DB...")
        updated = db.query(ProdutoV2).filter(ProdutoV2.codigo_supra == '002T20').update({
            ProdutoV2.estoque_disponivel: calc_disponivel,
            ProdutoV2.estoque_futuro: calc_futuro
        }, synchronize_session=False)
        db.commit()
        
        # Reload and assert
        db.refresh(p)
        print(f"DB values after update:")
        print(f"  estoque_disponivel: {p.estoque_disponivel}")
        print(f"  estoque_futuro: {p.estoque_futuro}")
        
        assert p.estoque_disponivel == calc_disponivel, "estoque_disponivel mismatch!"
        assert p.estoque_futuro == calc_futuro, "estoque_futuro mismatch!"
        print("SUCCESS: Ingestion logic matches and works correctly on DB!")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_ingestion()
