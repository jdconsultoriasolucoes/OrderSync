from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.error_log import ErrorLog
from schemas.error_log import ErrorLogCreate
from core.deps import get_current_user_optional

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.post("/erro")
def log_erro(
    log_in: ErrorLogCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user_optional)
):
    """Grava um log de erro vindo do frontend."""
    user_id = current_user.id if current_user else None
    
    novo_log = ErrorLog(
        usuario_id=user_id,
        modulo=log_in.modulo,
        status_code=log_in.status_code,
        mensagem=log_in.mensagem,
        payload=log_in.payload
    )
    
    db.add(novo_log)
    db.commit()
    
    return {"status": "ok", "message": "Erro logado com sucesso"}
