import os
from database import SessionLocal
from sqlalchemy import text

def check():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tb_pedidos';"))
        print("Columns in tb_pedidos:")
        for r in res.fetchall():
            print(f"- {r[0]} ({r[1]})")
            
        print("\nChecking if there's any calcula_st in tb_pedidos...")
        res_st = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_pedidos' AND column_name = 'calcula_st';")).scalar()
        print(f"calcula_st exists in tb_pedidos: {res_st is not None}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
