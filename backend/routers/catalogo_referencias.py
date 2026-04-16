from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from typing import List

from database import SessionLocal

# Models
from models.catalogo_referencias import (
    CanalVendaModel,
    CidadeSupervisorModel,
    MunicipioRotaModel,
    ReferenciasModel,
    SupervisoresModel,
    PlantelAnimalModel
)

# Schemas
from schemas.catalogo_referencias import (
    CanalVendaCreate, CanalVendaUpdate, CanalVendaResponse,
    CidadeSupervisorCreate, CidadeSupervisorUpdate, CidadeSupervisorResponse,
    MunicipioRotaCreate, MunicipioRotaUpdate, MunicipioRotaResponse,
    ReferenciasCreate, ReferenciasUpdate, ReferenciasResponse,
    SupervisoresCreate, SupervisoresUpdate, SupervisoresResponse,
    PlantelAnimalCreate, PlantelAnimalUpdate, PlantelAnimalResponse
)

router = APIRouter(
    prefix="/catalogo",
    tags=["Catalogo de Referencias"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helpers ---
def create_item(db: Session, model_class, item_data):
    db_item = model_class(**item_data.dict(exclude_unset=True))
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def update_item(db: Session, model_class, pk_field: str, item_id: int, item_data):
    # Depending on PK name we find it
    filter_expr = getattr(model_class, pk_field) == item_id
    db_item = db.query(model_class).filter(filter_expr).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def delete_item(db: Session, model_class, pk_field: str, item_id: int):
    filter_expr = getattr(model_class, pk_field) == item_id
    db_item = db.query(model_class).filter(filter_expr).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        db.delete(db_item)
        db.commit()
        return {"detail": "Item deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================================
# 1. CANAL DE VENDA
# ==========================================================

@router.get("/canal-venda", response_model=List[CanalVendaResponse])
def get_canais_venda(db: Session = Depends(get_db)):
    return db.query(CanalVendaModel).order_by(CanalVendaModel.Id).all()

@router.get("/canal-venda/{item_id}", response_model=CanalVendaResponse)
def get_canal_venda(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CanalVendaModel).filter(CanalVendaModel.Id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item

@router.post("/canal-venda", response_model=CanalVendaResponse)
def create_canal_venda(item: CanalVendaCreate, db: Session = Depends(get_db)): #, user: dict = Depends(get_current_user)
    return create_item(db, CanalVendaModel, item)

@router.put("/canal-venda/{item_id}", response_model=CanalVendaResponse)
def update_canal_venda(item_id: int, item: CanalVendaUpdate, db: Session = Depends(get_db)): #, user: dict = Depends(get_current_user)
    return update_item(db, CanalVendaModel, "Id", item_id, item)

@router.delete("/canal-venda/{item_id}")
def delete_canal_venda(item_id: int, db: Session = Depends(get_db)): #, user: dict = Depends(get_current_user)
    return delete_item(db, CanalVendaModel, "Id", item_id)

# ==========================================================
# 2. CIDADE SUPERVISOR
# ==========================================================

@router.get("/cidade-supervisor", response_model=List[CidadeSupervisorResponse])
def get_cidade_supervisores(db: Session = Depends(get_db)):
    return db.query(CidadeSupervisorModel).order_by(CidadeSupervisorModel.codigo).all()

import unicodedata

def _remove_accents(input_str: str) -> str:
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

@router.get("/cidade-supervisor/buscar")
def buscar_supervisor_por_municipio(municipio: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """
    Busca nome e códigos de supervisor (Pet e Insumos) baseando-se no município.
    Usado para preenchimento automático na tela de cadastro do cliente.
    """
    # 1. Tenta a busca básica ignorando case (pode falhar por causa dos acentos)
    item = db.query(CidadeSupervisorModel).filter(
        func.lower(CidadeSupervisorModel.cidades).like(f"%{municipio.lower()}%")
    ).first()
    
    # 2. Se falhar, busca na memória sem os acentos (Fallback)
    if not item:
        search_term = _remove_accents(municipio.lower())
        todos = db.query(CidadeSupervisorModel).all()
        for cidade_bd in todos:
            if cidade_bd.cidades:
                db_term = _remove_accents(cidade_bd.cidades.lower())
                if search_term in db_term or db_term in search_term:
                    item = cidade_bd
                    break

    if not item:
        raise HTTPException(status_code=404, detail="Município não encontrado na tabela de supervisores.")
        
    return {
        "codigo_insumo": str(item.numero_supervisor_insumos) if item.numero_supervisor_insumos else "",
        "nome_insumos": item.nome_supervisor_insumos or "",
        "codigo_pet": str(item.numero_supervisor_pet) if item.numero_supervisor_pet else "",
        "nome_pet": item.nome_supervisor_pet or "",
        "gerente_insumos": item.gerente_insumos or "",
        "gerente_pet": item.gerente_pet or ""
    }

@router.post("/cidade-supervisor", response_model=CidadeSupervisorResponse)
def create_cidade_supervisor(item: CidadeSupervisorCreate, db: Session = Depends(get_db)):
    return create_item(db, CidadeSupervisorModel, item)

@router.put("/cidade-supervisor/{item_id}", response_model=CidadeSupervisorResponse)
def update_cidade_supervisor(item_id: int, item: CidadeSupervisorUpdate, db: Session = Depends(get_db)):
    return update_item(db, CidadeSupervisorModel, "codigo", item_id, item)

@router.delete("/cidade-supervisor/{item_id}")
def delete_cidade_supervisor(item_id: int, db: Session = Depends(get_db)):
    return delete_item(db, CidadeSupervisorModel, "codigo", item_id)


# ==========================================================
# 3. MUNICÍPIO ROTA
# ==========================================================

@router.get("/municipio-rota", response_model=List[MunicipioRotaResponse])
def get_municipios_rota(db: Session = Depends(get_db)):
    return db.query(MunicipioRotaModel).order_by(MunicipioRotaModel.id).all()

@router.post("/municipio-rota", response_model=MunicipioRotaResponse)
def create_municipio_rota(item: MunicipioRotaCreate, db: Session = Depends(get_db)):
    return create_item(db, MunicipioRotaModel, item)

@router.put("/municipio-rota/{item_id}", response_model=MunicipioRotaResponse)
def update_municipio_rota(item_id: int, item: MunicipioRotaUpdate, db: Session = Depends(get_db)):
    return update_item(db, MunicipioRotaModel, "id", item_id, item)

@router.delete("/municipio-rota/{item_id}")
def delete_municipio_rota(item_id: int, db: Session = Depends(get_db)):
    return delete_item(db, MunicipioRotaModel, "id", item_id)

# ==========================================================
# 4. REFERÊNCIAS
# ==========================================================

@router.get("/referencias", response_model=List[ReferenciasResponse])
def get_referencias(db: Session = Depends(get_db)):
    return db.query(ReferenciasModel).order_by(ReferenciasModel.codigo).all()

@router.post("/referencias", response_model=ReferenciasResponse)
def create_referencias(item: ReferenciasCreate, db: Session = Depends(get_db)):
    return create_item(db, ReferenciasModel, item)

@router.put("/referencias/{item_id}", response_model=ReferenciasResponse)
def update_referencias(item_id: int, item: ReferenciasUpdate, db: Session = Depends(get_db)):
    return update_item(db, ReferenciasModel, "codigo", item_id, item)

@router.delete("/referencias/{item_id}")
def delete_referencias(item_id: int, db: Session = Depends(get_db)):
    return delete_item(db, ReferenciasModel, "codigo", item_id)

# ==========================================================
# 5. SUPERVISORES
# ==========================================================

@router.get("/supervisores", response_model=List[SupervisoresResponse])
def get_supervisores(db: Session = Depends(get_db)):
    return db.query(SupervisoresModel).order_by(SupervisoresModel.id).all()

@router.post("/supervisores", response_model=SupervisoresResponse)
def create_supervisores(item: SupervisoresCreate, db: Session = Depends(get_db)):
    return create_item(db, SupervisoresModel, item)

@router.put("/supervisores/{item_id}", response_model=SupervisoresResponse)
def update_supervisores(item_id: int, item: SupervisoresUpdate, db: Session = Depends(get_db)):
    return update_item(db, SupervisoresModel, "id", item_id, item)

@router.delete("/supervisores/{item_id}")
def delete_supervisores(item_id: int, db: Session = Depends(get_db)):
    return delete_item(db, SupervisoresModel, "id", item_id)


# ==========================================================
# 6. PLANTEL ANIMAIS
# ==========================================================

@router.get("/plantel-animais", response_model=List[PlantelAnimalResponse])
def get_plantel_animais(db: Session = Depends(get_db)):
    return db.query(PlantelAnimalModel).order_by(PlantelAnimalModel.id).all()

@router.post("/plantel-animais", response_model=PlantelAnimalResponse)
def create_plantel_animais(item: PlantelAnimalCreate, db: Session = Depends(get_db)):
    return create_item(db, PlantelAnimalModel, item)

@router.put("/plantel-animais/{item_id}", response_model=PlantelAnimalResponse)
def update_plantel_animais(item_id: int, item: PlantelAnimalUpdate, db: Session = Depends(get_db)):
    return update_item(db, PlantelAnimalModel, "id", item_id, item)

@router.delete("/plantel-animais/{item_id}")
def delete_plantel_animais(item_id: int, db: Session = Depends(get_db)):
    return delete_item(db, PlantelAnimalModel, "id", item_id)
