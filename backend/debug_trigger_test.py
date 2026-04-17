import os
import sys

# Injeta a URL no sistema 
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import SessionLocal
from models.catalogo_referencias import CidadeSupervisorModel
from services.sync_service import sync_cidade_supervisor

db = SessionLocal()
item = db.query(CidadeSupervisorModel).first()
if item:
    print(f"Testando cidade_supervisor com municipio: {item.cidades}")
    try:
        sync_cidade_supervisor(db, item.cidades, item)
        print("Sucesso!")
    except Exception as e:
        print(f"Erro capturado no python local: {e}")
else:
    print("Nenhum item na db!")
