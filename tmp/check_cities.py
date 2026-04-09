import sys
sys.path.append('e:/OrderSync/backend')
from database import SessionLocal
from models.catalogo_referencias import CidadeSupervisorModel
import unicodedata

db = SessionLocal()
count = db.query(CidadeSupervisorModel).count()
print(f"Total cities: {count}")
for c in db.query(CidadeSupervisorModel).limit(5).all():
    print(c.cidades)
