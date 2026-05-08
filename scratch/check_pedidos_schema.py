from sqlalchemy import text
from database import SessionLocal

def check_columns():
    db = SessionLocal()
    try:
        # Check columns of tb_pedidos
        res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_pedidos'")).fetchall()
        print("Columns in tb_pedidos:")
        for r in res:
            print(f"- {r[0]}")
        
        # Check some data
        res = db.execute(text("SELECT id_pedido, pedido_supra, nota_fiscal FROM tb_pedidos LIMIT 10")).fetchall()
        print("\nSample Data:")
        for r in res:
            print(f"ID: {r[0]}, Supra: {r[1]}, NF: {r[2]}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_columns()
