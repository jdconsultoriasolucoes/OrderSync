import os
import sys
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

os.environ["DATABASE_URL"] = DB_URL 

# Setup path
sys.path.append(r"e:\OrderSync\backend")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.pdf_service import gerar_pdf_pedido
from services.pedido_pdf_data import carregar_pedido_pdf

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get recent confirmed pedido
res = session.execute(text("SELECT id_pedido FROM tb_pedidos ORDER BY id_pedido DESC LIMIT 1")).scalar()

if not res:
    print("No confirmed pedidos found to test PDF.")
    exit(1)

pedido_id = res
print(f"Generating PDF for Pedido ID: {pedido_id}")

try:
    # Test new 'bytes' generation method
    pdf_bytes = gerar_pdf_pedido(session, pedido_id)
    
    out_path = f"debug_pedido_{pedido_id}.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
        
    print(f"PDF saved to {out_path} ({len(pdf_bytes)} bytes)")
    print("Please inspect this file manually to see if it is corrupt.")
    
except Exception as e:
    print("CRASHED during PDF generation!")
    import traceback
    traceback.print_exc()

session.close()
