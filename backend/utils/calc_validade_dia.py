from datetime import date
from typing import Optional, Literal

StatusValidade = Literal["ok", "alerta", "expirada", "nao_definida"]

def dias_restantes(validade: Optional[date], hoje: Optional[date] = None) -> Optional[int]:
    if validade is None:
        return None
    hoje = hoje or date.today()
    return (validade - hoje).days

def classificar_status(dias: Optional[int]) -> StatusValidade:
    if dias is None:
        return "nao_definida"
    if dias < 0:
        return "expirada"
    if dias <= 7:
        return "alerta"
    return "ok"