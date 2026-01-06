import os
import sys
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")

# 1. Setup Env
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

os.environ["DATABASE_URL"] = DB_URL # Critical for database.py

# 2. Setup Modules
sys.path.append(r"e:\OrderSync\backend")

# 3. Imports causing side-effects
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.link_pedido import resolver_code

# 4. Execution
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

last_code = session.execute(text("SELECT code FROM tb_pedido_link ORDER BY created_at DESC LIMIT 1")).scalar()

if not last_code:
    # Try alternate table name if t_pedido_links/tb_pedido_link confusion exists
    try:
        last_code = session.execute(text("SELECT code FROM t_pedido_links ORDER BY created_at DESC LIMIT 1")).scalar()
    except:
        pass

if not last_code:
    print("No links found in DB to test.")
else:
    print(f"Testing resolution for code: {last_code}")
    try:
        link, status = resolver_code(session, last_code)
        print("Success!")
        print(f"Status: {status}")
        print(f"Link Obj: {link}")
    except Exception as e:
        print("CRASHED!")
        import traceback
        traceback.print_exc()

session.close()
