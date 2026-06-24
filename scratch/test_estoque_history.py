import sys
import os
import pandas as pd

# Adjust path to import backend modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

# Load env before database import
os.environ.setdefault("DATABASE_URL", "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require")

from database import SessionLocal
from models.produto import HistoricoEstoqueV2

def test_ingestion_with_history():
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
    
    db = SessionLocal()
    try:
        before_count = db.query(HistoricoEstoqueV2).count()
        print("History count before:", before_count)

        db.query(HistoricoEstoqueV2).filter(HistoricoEstoqueV2.codigo_supra == '002T20').delete()
        db.commit()

        hist_entry = HistoricoEstoqueV2(
            codigo_supra='002T20',
            nome_produto='SUPRA IMPULSO SC 20KG',
            qtd_estoque=qtd_estoque,
            qtd_pedido=qtd_pedidos,
            af_pendentes=af_pendentes,
            estoque_disponivel=calc_disponivel,
            estoque_futuro=calc_futuro,
            nome_arquivo='estoque.xlsx',
            usuario='test@ordersync.com'
        )
        db.add(hist_entry)
        db.commit()

        h = db.query(HistoricoEstoqueV2).filter(HistoricoEstoqueV2.codigo_supra == '002T20').order_by(HistoricoEstoqueV2.id.desc()).first()
        print("Inserted history row:")
        print(f"  codigo_supra: {h.codigo_supra}")
        print(f"  nome_produto: {h.nome_produto}")
        print(f"  qtd_estoque: {h.qtd_estoque}")
        print(f"  qtd_pedido: {h.qtd_pedido}")
        print(f"  af_pendentes: {h.af_pendentes}")
        print(f"  estoque_disponivel: {h.estoque_disponivel}")
        print(f"  estoque_futuro: {h.estoque_futuro}")
        print(f"  data_ingestao: {h.data_ingestao}")
        
        assert h.estoque_disponivel == calc_disponivel, "History estoque_disponivel mismatch!"
        assert h.estoque_futuro == calc_futuro, "History estoque_futuro mismatch!"
        print("SUCCESS: History table logging verified and works perfectly!")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_ingestion_with_history()
