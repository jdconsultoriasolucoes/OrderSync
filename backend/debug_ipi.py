from database import SessionLocal
from sqlalchemy import text

def debug_product(codigo):
    db = SessionLocal()
    try:
        print(f"--- Debugging Product {codigo} ---")
        # Get Product ID
        res = db.execute(text("SELECT id, nome_produto, peso FROM t_cadastro_produto_v2 WHERE codigo_supra = :c"), {"c": codigo}).mappings().first()
        if not res:
            print("Product not found")
            return
        
        pid = res['id']
        print(f"ID: {pid}, Name: {res['nome_produto']}, Weight: {res['peso']}")

        # Get Tax
        tax = db.execute(text("SELECT ipi, iva_st, icms FROM t_imposto_v2 WHERE produto_id = :pid"), {"pid": pid}).mappings().first()
        if tax:
            print(f"Tax Data: IPI={tax['ipi']}, IVA_ST={tax['iva_st']}, ICMS={tax['icms']}")
        else:
            print("No tax data found in t_imposto_v2")

    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    debug_product("1431E5")
