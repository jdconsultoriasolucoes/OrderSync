from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.deps import get_db, get_current_user
from models.usuario import UsuarioModel
from models.calendario import CalendarModel, CalendarShareModel
from schemas.calendario import CalendarCreate, CalendarResponse, CalendarShareCreate, CalendarShareResponse

router = APIRouter(prefix="/calendars", tags=["Calendários"])

@router.get("", response_model=List[CalendarResponse])
def get_calendars(db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_user)):
    # Agendas próprias
    own_calendars = db.query(CalendarModel).filter(CalendarModel.user_id == current_user.id).all()
    
    # Agendas compartilhadas
    shared_calendars = db.query(CalendarModel).join(CalendarShareModel).filter(
        CalendarShareModel.shared_with_user_id == current_user.id
    ).all()
    
    # Formatar resposta para injetar o permission_level
    results = []
    for cal in own_calendars:
        res = CalendarResponse.model_validate(cal)
        res.permission_level = "admin"
        results.append(res)
        
    for cal in shared_calendars:
        share = db.query(CalendarShareModel).filter(
            CalendarShareModel.calendar_id == cal.id,
            CalendarShareModel.shared_with_user_id == current_user.id
        ).first()
        res = CalendarResponse.model_validate(cal)
        res.permission_level = share.permission_level if share else "read"
        results.append(res)
        
    return results

@router.post("", response_model=CalendarResponse)
def create_calendar(
    calendar: CalendarCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    db_calendar = CalendarModel(
        user_id=current_user.id,
        name=calendar.name,
        color=calendar.color,
        is_default=False
    )
    db.add(db_calendar)
    db.commit()
    db.refresh(db_calendar)
    return db_calendar

@router.post("/{calendar_id}/share", response_model=CalendarShareResponse)
def share_calendar(
    calendar_id: UUID,
    share_data: CalendarShareCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Verificar se o calendário pertence ao usuário ou se ele é admin
    calendar = db.query(CalendarModel).filter(CalendarModel.id == calendar_id).first()
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendário não encontrado")
        
    is_owner = calendar.user_id == current_user.id
    is_admin = False
    
    if not is_owner:
        share = db.query(CalendarShareModel).filter(
            CalendarShareModel.calendar_id == calendar_id,
            CalendarShareModel.shared_with_user_id == current_user.id
        ).first()
        if share and share.permission_level == "admin":
            is_admin = True
            
    if not is_owner and not is_admin:
        raise HTTPException(status_code=403, detail="Sem permissão para compartilhar esta agenda")
        
    # Encontrar usuário alvo
    target_user = db.query(UsuarioModel).filter(UsuarioModel.email == share_data.shared_with_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário alvo não encontrado")
        
    # Verificar se já existe compartilhamento
    existing_share = db.query(CalendarShareModel).filter(
        CalendarShareModel.calendar_id == calendar_id,
        CalendarShareModel.shared_with_user_id == target_user.id
    ).first()
    
    if existing_share:
        # Atualiza a permissão
        existing_share.permission_level = share_data.permission_level
        db.commit()
        db.refresh(existing_share)
        return existing_share
        
    # Cria novo
    new_share = CalendarShareModel(
        calendar_id=calendar_id,
        shared_with_user_id=target_user.id,
        permission_level=share_data.permission_level
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    return new_share

@router.delete("/{calendar_id}")
def delete_calendar(
    calendar_id: UUID,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    calendar = db.query(CalendarModel).filter(CalendarModel.id == calendar_id).first()
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendário não encontrado")
        
    if calendar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o dono pode deletar a agenda")
        
    if calendar.is_default:
        raise HTTPException(status_code=400, detail="Não é possível deletar a agenda padrão")
        
    db.delete(calendar)
    db.commit()
    return {"message": "Agenda deletada com sucesso"}
