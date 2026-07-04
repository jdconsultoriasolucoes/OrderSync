from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class ErrorLogCreate(BaseModel):
    modulo: str
    status_code: Optional[int] = None
    mensagem: str
    payload: Optional[Any] = None

class ErrorLogResponse(ErrorLogCreate):
    id: int
    usuario_id: Optional[int] = None
    data_hora: datetime

    class Config:
        from_attributes = True
