from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date
from uuid import UUID
from sqlalchemy import or_

from core.deps import get_db, get_current_user
from models.usuario import UsuarioModel
from models.calendario import EventModel, CalendarModel, CalendarShareModel, EventShareModel
from models.cliente_v2 import ClienteModelV2
from schemas.calendario import EventCreate, EventUpdate, EventWithCalendarResponse, EventShareCreate, EventShareResponse

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

def _check_event_access(db: Session, event_id: UUID, user_id: int, required_permission: str = "read"):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        return None, "Evento não encontrado"
        
    calendar, cal_perm = _check_calendar_access(db, event.calendar_id, user_id, "read")
    
    if cal_perm in ["admin", "write"]:
        return event, cal_perm
        
    if cal_perm == "read" and required_permission == "read":
        return event, "read"
        
    share = db.query(EventShareModel).filter(
        EventShareModel.event_id == event_id,
        EventShareModel.shared_with_user_id == user_id
    ).first()
    
    if not share:
        return None, "Acesso negado"
        
    perms_hierarchy = {"read": 1, "write": 2, "admin": 3}
    if perms_hierarchy.get(share.permission_level, 0) < perms_hierarchy.get(required_permission, 1):
        return None, "Permissão insuficiente"
        
    return event, share.permission_level

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
    
    shared_events = db.query(EventShareModel).filter(EventShareModel.shared_with_user_id == current_user.id).all()
    shared_events_ids = [s.event_id for s in shared_events]
    
    # Busca otimizada por intervalo
    events = db.query(EventModel).filter(
        or_(
            EventModel.calendar_id.in_(all_calendar_ids),
            EventModel.id.in_(shared_events_ids)
        ),
        EventModel.start_time >= start_date,
        EventModel.start_time <= end_date
    ).all()
    
    # Formatar resposta
    results = []
    for ev in events:
        res = EventWithCalendarResponse.model_validate(ev)
        calendar = db.query(CalendarModel).filter(CalendarModel.id == ev.calendar_id).first()
        res.calendar_color = calendar.color if calendar else "#3182ce"
        res.calendar_name = calendar.name if calendar else "Compartilhado"
        
        if calendar and calendar.user_id == current_user.id:
            res.permission_level = "admin"
        else:
            share_cal = next((s for s in shared_calendars if s.calendar_id == ev.calendar_id), None)
            if share_cal:
                res.permission_level = share_cal.permission_level
            else:
                share_ev = next((s for s in shared_events if s.event_id == ev.id), None)
                res.permission_level = share_ev.permission_level if share_ev else "read"
                
        if ev.cliente_id:
            cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == ev.cliente_id).first()
            if cliente:
                res.cliente_nome = cliente.cadastro_nome_cliente or cliente.cadastro_nome_fantasia
                res.cliente_telefone = cliente.compras_celular_responsavel or cliente.legal_celular
                
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
        location=event.location,
        cliente_id=event.cliente_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    res = EventWithCalendarResponse.model_validate(db_event)
    res.calendar_color = calendar.color
    res.calendar_name = calendar.name
    res.permission_level = perm
    
    if db_event.cliente_id:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == db_event.cliente_id).first()
        if cliente:
            res.cliente_nome = cliente.cadastro_nome_cliente or cliente.cadastro_nome_fantasia
            res.cliente_telefone = cliente.compras_celular_responsavel or cliente.legal_celular
            
    return res

@router.put("/{event_id}", response_model=EventWithCalendarResponse)
def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    db_event, perm = _check_event_access(db, event_id, current_user.id, "write")
    if not db_event:
        raise HTTPException(status_code=403, detail=perm or "Acesso negado")
        
    for var, value in vars(event_update).items():
        if value is not None:
            setattr(db_event, var, value)
            
    db.commit()
    db.refresh(db_event)
    
    res = EventWithCalendarResponse.model_validate(db_event)
    calendar = db.query(CalendarModel).filter(CalendarModel.id == db_event.calendar_id).first()
    res.calendar_color = calendar.color if calendar else "#3182ce"
    res.calendar_name = calendar.name if calendar else "Compartilhado"
    res.permission_level = perm
    
    if db_event.cliente_id:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == db_event.cliente_id).first()
        if cliente:
            res.cliente_nome = cliente.cadastro_nome_cliente or cliente.cadastro_nome_fantasia
            res.cliente_telefone = cliente.compras_celular_responsavel or cliente.legal_celular
            
    return res

@router.delete("/{event_id}")
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    db_event, perm = _check_event_access(db, event_id, current_user.id, "write")
    if not db_event:
        raise HTTPException(status_code=403, detail=perm or "Acesso negado")
        
    db.delete(db_event)
    db.commit()
    return {"message": "Evento deletado com sucesso"}

@router.post("/{event_id}/share", response_model=EventShareResponse)
def share_event(
    event_id: UUID,
    share_data: EventShareCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    event, perm = _check_event_access(db, event_id, current_user.id, "write")
    if not event or perm == "read":
        raise HTTPException(status_code=403, detail="Sem permissão para compartilhar este evento")
        
    target_user = db.query(UsuarioModel).filter(UsuarioModel.email == share_data.shared_with_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário alvo não encontrado")
        
    existing_share = db.query(EventShareModel).filter(
        EventShareModel.event_id == event_id,
        EventShareModel.shared_with_user_id == target_user.id
    ).first()
    
    if existing_share:
        existing_share.permission_level = share_data.permission_level
        db.commit()
        db.refresh(existing_share)
        return existing_share
        
    new_share = EventShareModel(
        event_id=event_id,
        shared_with_user_id=target_user.id,
        permission_level=share_data.permission_level
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    return new_share
