from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
from sqlalchemy import or_, text
from zoneinfo import ZoneInfo

from core.deps import get_db, get_current_user
from models.usuario import UsuarioModel
from models.calendario import EventModel, CalendarModel, CalendarShareModel, EventShareModel, EventAuditoriaModel
from models.cliente_v2 import ClienteModelV2
from schemas.calendario import EventCreate, EventUpdate, EventWithCalendarResponse, EventShareCreate, EventShareResponse

router = APIRouter(prefix="/events", tags=["Eventos"])

tz_sp = ZoneInfo("America/Sao_Paulo")

def _to_sp(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz_sp)
    return dt.astimezone(tz_sp)

def _garantir_tabela_evento_auditoria(db: Session):
    try:
        with db.begin_nested():
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS public.tb_eventos_auditoria (
                    id BIGSERIAL PRIMARY KEY,
                    event_id UUID NOT NULL,
                    usuario_id BIGINT,
                    usuario_nome VARCHAR(255),
                    usuario_email VARCHAR(255),
                    acao VARCHAR(50) NOT NULL,
                    detalhes TEXT,
                    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_tb_eventos_auditoria_event_id ON public.tb_eventos_auditoria (event_id);
            """))
    except Exception:
        pass

def _registrar_auditoria_evento(db: Session, event_id: UUID, user: UsuarioModel, acao: str, detalhes: str):
    try:
        _garantir_tabela_evento_auditoria(db)
        log = EventAuditoriaModel(
            event_id=event_id,
            usuario_id=user.id,
            usuario_nome=user.nome or user.email,
            usuario_email=user.email,
            acao=acao,
            detalhes=detalhes,
            criado_em=datetime.now(tz_sp)
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()

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

def _preencher_detalhes_evento(db: Session, res: EventWithCalendarResponse, ev: EventModel):
    # Cliente
    if ev.cliente_id:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == ev.cliente_id).first()
        if cliente:
            res.cliente_nome = cliente.cadastro_nome_cliente or cliente.cadastro_nome_fantasia
            res.cliente_telefone = cliente.compras_celular_responsavel or cliente.legal_celular

    # Compartilhados
    shares_for_ev = db.query(EventShareModel).filter(EventShareModel.event_id == ev.id).all()
    shared_list = []
    for s in shares_for_ev:
        u = db.query(UsuarioModel).filter(UsuarioModel.id == s.shared_with_user_id).first()
        if u:
            shared_list.append({"id": str(s.id), "email": u.email, "permission_level": s.permission_level})
    res.shared_with = shared_list

    # Auditoria
    _garantir_tabela_evento_auditoria(db)
    auditorias = db.query(EventAuditoriaModel).filter(EventAuditoriaModel.event_id == ev.id).order_by(EventAuditoriaModel.criado_em.desc()).all()
    if auditorias:
        res.ultimo_autor = auditorias[0].usuario_nome or auditorias[0].usuario_email
        res.ultima_alteracao_em = auditorias[0].criado_em
        res.historico = [
            {
                "acao": a.acao,
                "usuario": a.usuario_nome or a.usuario_email or "Sistema",
                "detalhes": a.detalhes,
                "data_hora": _to_sp(a.criado_em).strftime("%d/%m/%Y %H:%M") if a.criado_em else None
            }
            for a in auditorias
        ]

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
    
    from datetime import timedelta
    
    # Busca otimizada por intervalo
    events = db.query(EventModel).filter(
        or_(
            EventModel.calendar_id.in_(all_calendar_ids),
            EventModel.id.in_(shared_events_ids)
        ),
        EventModel.start_time >= start_date,
        EventModel.start_time < (end_date + timedelta(days=1))
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
                
        _preencher_detalhes_evento(db, res, ev)
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
        
    # Validação de data/hora no passado
    now_sp = datetime.now(tz_sp)
    event_start_sp = _to_sp(event.start_time)
    if event_start_sp < now_sp:
        raise HTTPException(
            status_code=400,
            detail="Não é permitido agendar eventos em datas ou horários que já passaram."
        )

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
    
    if event.shared_with_users:
        for share_input in event.shared_with_users:
            target_user = db.query(UsuarioModel).filter(UsuarioModel.email == share_input.email).first()
            if target_user:
                new_share = EventShareModel(
                    event_id=db_event.id,
                    shared_with_user_id=target_user.id,
                    permission_level=share_input.permission_level
                )
                db.add(new_share)
        db.commit()
    
    # Registro de auditoria
    _registrar_auditoria_evento(
        db=db,
        event_id=db_event.id,
        user=current_user,
        acao="CRIACAO",
        detalhes=f"Evento criado para {event_start_sp.strftime('%d/%m/%Y %H:%M')}"
    )

    res = EventWithCalendarResponse.model_validate(db_event)
    res.calendar_color = calendar.color
    res.calendar_name = calendar.name
    res.permission_level = perm
    _preencher_detalhes_evento(db, res, db_event)

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
        
    now_sp = datetime.now(tz_sp)
    update_data = event_update.model_dump(exclude_unset=True)

    # Validação de alteração de horário para o passado
    if event_update.start_time is not None:
        new_start_sp = _to_sp(event_update.start_time)
        old_start_sp = _to_sp(db_event.start_time)
        # Se alterou o horário e a nova data/hora está no passado
        if new_start_sp != old_start_sp and new_start_sp < now_sp:
            raise HTTPException(
                status_code=400,
                detail="Não é permitido alterar eventos para datas ou horários que já passaram."
            )

    # Identificar alterações para auditoria
    mudancas = []
    if "title" in update_data and update_data["title"] != db_event.title:
        mudancas.append(f"Título alterado de '{db_event.title}' para '{update_data['title']}'")

    if "start_time" in update_data:
        old_st = _to_sp(db_event.start_time).strftime("%d/%m/%Y %H:%M")
        new_st = _to_sp(update_data["start_time"]).strftime("%d/%m/%Y %H:%M")
        if old_st != new_st:
            mudancas.append(f"Início alterado de {old_st} para {new_st}")

    if "end_time" in update_data:
        old_et = _to_sp(db_event.end_time).strftime("%d/%m/%Y %H:%M")
        new_et = _to_sp(update_data["end_time"]).strftime("%d/%m/%Y %H:%M")
        if old_et != new_et:
            mudancas.append(f"Fim alterado de {old_et} para {new_et}")

    if "location" in update_data and (update_data["location"] or "") != (db_event.location or ""):
        mudancas.append(f"Local alterado para '{update_data['location'] or ''}'")

    if "description" in update_data and (update_data["description"] or "") != (db_event.description or ""):
        mudancas.append("Descrição alterada")

    if "cliente_id" in update_data and update_data["cliente_id"] != db_event.cliente_id:
        old_nome = "Nenhum"
        if db_event.cliente_id:
            old_c = db.query(ClienteModelV2).filter(ClienteModelV2.id == db_event.cliente_id).first()
            if old_c:
                old_nome = old_c.cadastro_nome_cliente or old_c.cadastro_nome_fantasia or str(db_event.cliente_id)

        new_nome = "Nenhum"
        if update_data["cliente_id"]:
            new_c = db.query(ClienteModelV2).filter(ClienteModelV2.id == update_data["cliente_id"]).first()
            if new_c:
                new_nome = new_c.cadastro_nome_cliente or new_c.cadastro_nome_fantasia or str(update_data["cliente_id"])

        if update_data["cliente_id"] is None:
            mudancas.append(f"Cliente desvinculado (anterior: {old_nome})")
        elif db_event.cliente_id is None:
            mudancas.append(f"Cliente vinculado: {new_nome}")
        else:
            mudancas.append(f"Cliente alterado de {old_nome} para {new_nome}")

    # Atualizar campos no banco
    for field, value in update_data.items():
        if field != "shared_with_users":
            setattr(db_event, field, value)
            
    # Apenas admin da agenda pode alterar usuários compartilhados
    if perm == "admin" and "shared_with_users" in update_data and update_data["shared_with_users"] is not None:
        db.query(EventShareModel).filter(EventShareModel.event_id == db_event.id).delete()
        for share_input in event_update.shared_with_users:
            target_user = db.query(UsuarioModel).filter(UsuarioModel.email == share_input.email).first()
            if target_user:
                new_share = EventShareModel(
                    event_id=db_event.id,
                    shared_with_user_id=target_user.id,
                    permission_level=share_input.permission_level
                )
                db.add(new_share)

    db.commit()
    db.refresh(db_event)
    
    # Registrar histórico de auditoria
    if mudancas:
        _registrar_auditoria_evento(
            db=db,
            event_id=db_event.id,
            user=current_user,
            acao="EDICAO",
            detalhes="; ".join(mudancas)
        )
    
    res = EventWithCalendarResponse.model_validate(db_event)
    calendar = db.query(CalendarModel).filter(CalendarModel.id == db_event.calendar_id).first()
    res.calendar_color = calendar.color if calendar else "#3182ce"
    res.calendar_name = calendar.name if calendar else "Compartilhado"
    res.permission_level = perm
    _preencher_detalhes_evento(db, res, db_event)

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
        
    _registrar_auditoria_evento(
        db=db,
        event_id=db_event.id,
        user=current_user,
        acao="EXCLUSAO",
        detalhes=f"Evento '{db_event.title}' excluído"
    )
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

@router.delete("/{event_id}/share/{share_id}")
def remove_event_share(
    event_id: UUID,
    share_id: UUID,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    event, perm = _check_event_access(db, event_id, current_user.id, "write")
    if not event or perm == "read":
        raise HTTPException(status_code=403, detail="Sem permissão para alterar compartilhamentos")
        
    share = db.query(EventShareModel).filter(
        EventShareModel.id == share_id,
        EventShareModel.event_id == event_id
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")
        
    db.delete(share)
    db.commit()
    return {"message": "Compartilhamento removido com sucesso"}
