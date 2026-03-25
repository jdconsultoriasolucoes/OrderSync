from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.automation_config import AutomationConfigModel
from models.usuario import UsuarioModel
from core.deps import get_current_user
from pydantic import BaseModel
import datetime

router = APIRouter(
    prefix="/admin/automacao",
    tags=["Admin - Automação"],
)

class AutomationConfigBase(BaseModel):
    prospeccao_ativa: bool
    prospeccao_dia_semana: int
    prospeccao_horario: str # Formato "HH:MM" ou "HH:MM:SS"

@router.get("/config", response_model=AutomationConfigBase)
def get_automation_config(db: Session = Depends(get_db)):
    cfg = db.query(AutomationConfigModel).first()
    if not cfg:
        # Retorna padrão se não existir
        return AutomationConfigBase(
            prospeccao_ativa=False,
            prospeccao_dia_semana=0, # Segunda
            prospeccao_horario="08:00:00"
        )
        
    return AutomationConfigBase(
        prospeccao_ativa=cfg.prospeccao_ativa,
        prospeccao_dia_semana=cfg.prospeccao_dia_semana,
        prospeccao_horario=cfg.prospeccao_horario.strftime('%H:%M:%S') if cfg.prospeccao_horario else "08:00:00"
    )

@router.put("/config", response_model=AutomationConfigBase)
def update_automation_config(
    data: AutomationConfigBase,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    try:
        # Valida parse de hora
        parts = data.prospeccao_horario.split(":")
        hh = int(parts[0])
        mm = int(parts[1])
        parsed_time = datetime.time(hour=hh, minute=mm, second=0)
    except Exception:
        raise HTTPException(status_code=400, detail="Horário inválido. Use formato HH:MM.")

    cfg = db.query(AutomationConfigModel).first()
    if not cfg:
        cfg = AutomationConfigModel(
            prospeccao_ativa=data.prospeccao_ativa,
            prospeccao_dia_semana=data.prospeccao_dia_semana,
            prospeccao_horario=parsed_time
        )
        db.add(cfg)
    else:
        cfg.prospeccao_ativa = data.prospeccao_ativa
        cfg.prospeccao_dia_semana = data.prospeccao_dia_semana
        cfg.prospeccao_horario = parsed_time

    db.commit()
    return data

@router.post("/testar-prospeccao")
def trigger_prospeccao_agora(db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_user)):
    """ Endpoint oculto/dev para testar o envio de prospecção na hora """
    from services.prospeccao_service import enviar_relatorios_prospeccao
    from fastapi.background import BackgroundTasks
    
    # Para não travar a req, rodamas na bg_task do fastapi (não a do db, pra ser imediato)
    enviar_relatorios_prospeccao(db)
    
    return {"message": "Rotina de prospecção disparada com sucesso."}

