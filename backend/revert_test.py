from database import SessionLocal
from sqlalchemy import text

def revert():
    db = SessionLocal()
    try:
        db.execute(text("UPDATE tb_pedidos SET status='CONFIRMADO' WHERE id_pedido=46"))
        db.commit()
        print("Reverted order 46 to CONFIRMADO")
    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    revert()
