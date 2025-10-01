import secrets
from datetime import datetime, time
from sqlalchemy import text
from models.pedido_link import PedidoLink

def _fim_do_dia(d):  # date → datetime no fim do dia
    return datetime.combine(d, time(23, 59, 59, 999999))

def calcular_expires_at_global(db):
    v = db.execute(text("""
        SELECT MAX(CAST(p.validade_tabela AS DATE)) AS max_validade
        FROM t_cadastro_produto p
        WHERE p.status_produto = 'ATIVO'
    """)).scalar()
    return _fim_do_dia(v) if v else None

def gerar_link_code(db, tabela_id: int, com_frete: bool):
    code = secrets.token_urlsafe(12)[:16]
    expires_at = calcular_expires_at_global(db)
    link = PedidoLink(code=code, tabela_id=tabela_id, com_frete=com_frete, expires_at=expires_at)
    db.add(link)
    db.commit()
    return code, expires_at

def resolver_code(db, code: str):
    link = db.query(PedidoLink).get(code)
    if not link:
        return None, "not_found"
    if link.expires_at and datetime.utcnow() > link.expires_at:
        return None, "expired"
    return link, "ok"
