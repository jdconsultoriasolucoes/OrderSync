from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base
from sqlalchemy.orm import relationship

class CalendarModel(Base):
    __tablename__ = "calendars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(BigInteger, ForeignKey("t_usuario.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    shares = relationship("CalendarShareModel", back_populates="calendar", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="calendar", cascade="all, delete-orphan")

class CalendarShareModel(Base):
    __tablename__ = "calendar_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_with_user_id = Column(BigInteger, ForeignKey("t_usuario.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_level = Column(String(20), nullable=False) # 'read', 'write', 'admin'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    calendar = relationship("CalendarModel", back_populates="shares")

class EventModel(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("t_usuario.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    is_all_day = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    calendar = relationship("CalendarModel", back_populates="events")
