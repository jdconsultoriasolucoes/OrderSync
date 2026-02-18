from database import SessionLocal
from sqlalchemy import text

def debug_condicoes():
    db = SessionLocal()
    try:
        print(f"--- Debugging Payment Conditions ---")
        res = db.execute(text("SELECT codigo_prazo, prazo, custo FROM t_condicoes_pagamento WHERE ativo IS TRUE")).fetchall()
        for r in res:
            print(f"Code: {r.codigo_prazo} | Desc: {r.prazo} | Rate (custo): {r.custo}")

    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    debug_condicoes()
