
import sys
sys.path.append('e:/OrderSync/backend')

from database import SessionLocal, engine, Base
from schemas.cargas import CargaResponse
from models.cargas import CargaModel

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    carga = CargaModel(nome_carga='Teste')
    db.add(carga)
    db.commit()
    db.refresh(carga)
    resp = CargaResponse.model_validate(carga)
    print('Validated successfully!', resp.model_dump())
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()

