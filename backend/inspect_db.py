from database import SessionLocal
from sqlalchemy import text

def inspect():
    db = SessionLocal()
    try:
        # Postgres query to get column names
        res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_cadastro_produto_v2';"))
        cols = res.fetchall()
        print("Columns in t_cadastro_produto_v2:")
        for c in cols:
            print(f"- {c[0]} ({c[1]})")
    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect()
