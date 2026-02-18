from database import SessionLocal
from sqlalchemy import text

def inspect():
    db = SessionLocal()
    try:
        # Check if table exists and list columns
        res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_familia_produtos';"))
        cols = res.fetchall()
        if not cols:
            print("Table t_familia_produtos does not exist (or no columns found).")
            # Try checking families table just in case user meant that
            res2 = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_familia';"))
            cols2 = res2.fetchall()
            if cols2:
                print("Found t_familia instead:")
                for c in cols2:
                    print(f"- {c[0]} ({c[1]})")
        else:
            print("Columns in t_familia_produtos:")
            for c in cols:
                print(f"- {c[0]} ({c[1]})")
                
        # Also let's see some data samples to confirm 'marca' content
        if cols:
             res_data = db.execute(text("SELECT * FROM t_familia_produtos LIMIT 5"))
             print("\nData Sample:")
             for r in res_data:
                 print(r)

    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect()
