import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

# Load env before database import
os.environ.setdefault("DATABASE_URL", "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require")

from routers.tabela_preco import filtrar_produtos_para_tabela_preco, obter_tabela

def test_api():
    print("Testing /tabela_preco/produtos_filtro...")
    res_filter = filtrar_produtos_para_tabela_preco(q='002T20', page=1, page_size=5, grupo=None, tipo=None, fornecedor=None)
    print("Filter API result items count:", len(res_filter['items']))
    if res_filter['items']:
        item = res_filter['items'][0]
        print("First item columns:")
        for k, v in item.items():
            if "estoque" in k:
                print(f"  {k}: {v}")
                
    print("\nTesting /tabela_preco/{id} mapping...")
    from database import SessionLocal
    from models.tabela_preco import TabelaPreco as TabelaPrecoModel
    db = SessionLocal()
    try:
        t = db.query(TabelaPrecoModel).filter_by(ativo=True).first()
        if t:
            print(f"Found active table ID: {t.id_tabela}")
            res_tab = obter_tabela(t.id_tabela)
            if res_tab.get('produtos'):
                prod = res_tab['produtos'][0]
                print("First product stock keys:")
                for k, v in prod.items():
                    if "estoque" in k:
                        print(f"  {k}: {v}")
        else:
            print("No active table found in DB.")
    finally:
        db.close()

if __name__ == "__main__":
    test_api()
