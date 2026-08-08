from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class CalendarBase(BaseModel):
    name: str
    color: str

class CalendarCreate(CalendarBase):
    pass

class CalendarResponse(CalendarBase):
    id: UUID
    user_id: int
    is_default: bool
    created_at: datetime
    permission_level: Optional[str] = "admin" # Admin by default for the owner

    model_config = ConfigDict(from_attributes=True)

class CalendarShareCreate(BaseModel):
    shared_with_email: str
    permission_level: str # 'read', 'write', 'admin'

class CalendarShareResponse(BaseModel):
    id: UUID
    calendar_id: UUID
    shared_with_user_id: int
    permission_level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    location: Optional[str] = None
    calendar_id: UUID
    cliente_id: Optional[int] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    location: Optional[str] = None
    cliente_id: Optional[int] = None

class EventResponse(EventBase):
    id: UUID
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EventWithCalendarResponse(EventResponse):
    calendar_color: Optional[str] = None
    calendar_name: Optional[str] = None
    permission_level: Optional[str] = "admin"
    cliente_nome: Optional[str] = None
    cliente_telefone: Optional[str] = None

class EventShareCreate(BaseModel):
    shared_with_email: str
    permission_level: str # 'read', 'write'

class EventShareResponse(BaseModel):
    id: UUID
    event_id: UUID
    shared_with_user_id: int
    permission_level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
