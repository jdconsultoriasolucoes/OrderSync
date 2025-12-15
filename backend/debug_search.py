
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Mocking the missing env var if needed, or relying on system env
if "DATABASE_URL" not in os.environ:
    # Try to find it or ask user? I'll assume it's in the environment as per Step 762 error suggesting it wasn't
    # But wait, Step 762 says KeyError: 'DATABASE_URL'.
    # I need the connection string!
    # I will try to read it from .env or just hardcode if I found it.
    # User never gave me the string.
    # BUT, I saw 'database.py' uses os.environ["DATABASE_URL"].
    # I need to know what that value is.
    pass

# Hardcoding for debug based on previous context if possible, or using a fallback to check.
# Since I can't run python without the ENV var, this script might fail if I don't set it.
# I will try to source it from the system commands in the `run_command` tool.

from services.produto_pdf import list_produtos, _row_to_out
from database import SessionLocal

def test_search():
    db = SessionLocal()
    try:
        print("Testing search for '016T5*5'...")
        # Emulating the search logic
        q = "016T5*5"
        base = "SELECT * FROM v_produto_v2_preco WHERE 1=1"
        base += " AND (nome_produto ILIKE :q OR codigo_supra ILIKE :q)"
        params = {"q": f"%{q}%", "limit": 50, "offset": 0}
        base += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
        
        print(f"Executing Query: {base}")
        rows = db.execute(text(base), params).mappings().all()
        print(f"Rows found: {len(rows)}")
        
        results = [_row_to_out(db, r, include_imposto=False) for r in rows]
        print("Mapping successful!")
    except Exception as e:
        print("CAUGHT EXCEPTION:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_search()
