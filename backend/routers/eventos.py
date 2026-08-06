from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date
from uuid import UUID

from core.deps import get_db, get_current_user
from models.usuario import UsuarioModel
from models.calendario import EventModel, CalendarModel, CalendarShareModel
from schemas.calendario import EventCreate, EventUpdate, EventWithCalendarResponse

router = APIRouter(prefix="/events", tags=["Eventos"])

def _check_calendar_access(db: Session, calendar_id: UUID, user_id: int, required_permission: str = "read"):
    calendar = db.query(CalendarModel).filter(CalendarModel.id == calendar_id).first()
    if not calendar:
        return None, "Calendário não encontrado"
        
    if calendar.user_id == user_id:
        return calendar, "admin"
        
    share = db.query(CalendarShareModel).filter(
        CalendarShareModel.calendar_id == calendar_id,
        CalendarShareModel.shared_with_user_id == user_id
    ).first()
    
    if not share:
        return None, "Acesso negado"
        
    # Check permissions
    perms_hierarchy = {"read": 1, "write": 2, "admin": 3}
    if perms_hierarchy.get(share.permission_level, 0) < perms_hierarchy.get(required_permission, 1):
        return None, "Permissão insuficiente"
        
    return calendar, share.permission_level

@router.get("", response_model=List[EventWithCalendarResponse])
def get_events(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    # Agendas com acesso
    own_calendars_ids = [c.id for c in db.query(CalendarModel).filter(CalendarModel.user_id == current_user.id).all()]
    shared_calendars = db.query(CalendarShareModel).filter(CalendarShareModel.shared_with_user_id == current_user.id).all()
    shared_calendars_ids = [c.calendar_id for c in shared_calendars]
    
    all_calendar_ids = own_calendars_ids + shared_calendars_ids
    
    # Busca otimizada por intervalo
    events = db.query(EventModel).filter(
        EventModel.calendar_id.in_(all_calendar_ids),
        EventModel.start_time >= start_date,
        EventModel.start_time <= end_date
    ).all()
    
    # Formatar resposta
    results = []
    for ev in events:
        res = EventWithCalendarResponse.model_validate(ev)
        calendar = db.query(CalendarModel).filter(CalendarModel.id == ev.calendar_id).first()
        res.calendar_color = calendar.color
        res.calendar_name = calendar.name
        
        if calendar.user_id == current_user.id:
            res.permission_level = "admin"
        else:
            share = next((s for s in shared_calendars if s.calendar_id == ev.calendar_id), None)
            res.permission_level = share.permission_level if share else "read"
            
        results.append(res)
        
    return results

@router.post("", response_model=EventWithCalendarResponse)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    calendar, perm = _check_calendar_access(db, event.calendar_id, current_user.id, "write")
    if not calendar:
        raise HTTPException(status_code=403, detail=perm)
        
    db_event = EventModel(
        calendar_id=event.calendar_id,
        created_by_user_id=current_user.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        is_all_day=event.is_all_day,
        location=event.location
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    res = EventWithCalendarResponse.model_validate(db_event)
    res.calendar_color = calendar.color
    res.calendar_name = calendar.name
    res.permission_level = perm
    return res

@router.put("/{event_id}", response_model=EventWithCalendarResponse)
def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
        
    calendar, perm = _check_calendar_access(db, db_event.calendar_id, current_user.id, "write")
    if not calendar:
        raise HTTPException(status_code=403, detail=perm)
        
    for var, value in vars(event_update).items():
        if value is not None:
            setattr(db_event, var, value)
            
    db.commit()
    db.refresh(db_event)
    
    res = EventWithCalendarResponse.model_validate(db_event)
    res.calendar_color = calendar.color
    res.calendar_name = calendar.name
    res.permission_level = perm
    return res

@router.delete("/{event_id}")
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
        
    calendar, perm = _check_calendar_access(db, db_event.calendar_id, current_user.id, "write")
    if not calendar:
        raise HTTPException(status_code=403, detail=perm)
        
    db.delete(db_event)
    db.commit()
    return {"message": "Evento deletado com sucesso"}
