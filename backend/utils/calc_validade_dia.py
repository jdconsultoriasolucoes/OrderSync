from datetime import date, datetime
from typing import Optional, Literal

StatusValidade = Literal["ok", "alerta", "expirada", "nao_definida"]

def _as_date(v: Optional[object]) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    # se vier string 'YYYY-MM-DD'
    try:
        return date.fromisoformat(str(v)[:10])
    except Exception:
        return None

def dias_restantes(validade: Optional[object], hoje: Optional[date] = None) -> Optional[int]:
    v = _as_date(validade)
    if v is None:
        return None
    hoje = hoje or date.today()
    return (v - hoje).days

def classificar_status(dias: Optional[int]) -> StatusValidade:
    if dias is None:
        return "nao_definida"
    if dias < 0:
        return "expirada"
    if dias <= 7:
        return "alerta"
    return "ok"
