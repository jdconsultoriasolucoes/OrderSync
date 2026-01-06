import secrets
from datetime import datetime, time
from sqlalchemy import text
from models.pedido_link import PedidoLink
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

def _fim_do_dia(d):  # date → datetime no fim do dia
    return datetime.combine(d, time(23, 59, 59, 999999))

def calcular_expires_at_global(db):
    v = db.execute(text("""
        SELECT MAX(CAST(p.validade_tabela AS DATE)) AS max_validade
        FROM t_cadastro_produto_v2 p
        WHERE p.status_produto = 'ATIVO'
    """)).scalar()
    return _fim_do_dia(v) if v else None

def _parse_iso_date(s):
    """Converte 'YYYY-MM-DD' em date; se for inválido ou None, retorna None."""
    if not isinstance(s, str) or len(s) != 10:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

def gerar_link_code(db, tabela_id: int, com_frete: bool, data_prevista_str: str | None = None, codigo_cliente: str | None = None):
    """
    Cria um link curto para a tabela.
    - data_prevista_str: string 'YYYY-MM-DD' (opcional). Será gravada em tb_pedido_link.data_prevista.
    Retorna: (code, expires_at, data_prevista)
    """
    code = secrets.token_urlsafe(12)[:16]
    expires_at = calcular_expires_at_global(db)
    data_prevista = _parse_iso_date(data_prevista_str)

    cod = (codigo_cliente or "").strip() or "Não cadastrado"
    cod = cod[:80]
    
    link = PedidoLink(
        code=code,
        tabela_id=tabela_id,
        com_frete=com_frete,
        data_prevista=data_prevista, 
        expires_at=expires_at,
        codigo_cliente=cod
    )
    db.add(link)
    db.commit()

    return code, expires_at, data_prevista

def resolver_code(db, code: str):
    """
    Busca o link pelo code. Se expirado, retorna ('expired').
    Se ok, incrementa contador de uso e retorna (link, 'ok').
    """
    link = db.query(PedidoLink).get(code)
    if not link:
        return None, "not_found"
    if link.expires_at and datetime.now(TZ) > link.expires_at:
        return link, "expired"

    # contadores e carimbos
    now = datetime.now(TZ)
    db.execute(text("""
        UPDATE tb_pedido_link
           SET uses = COALESCE(uses,0) + 1,
               first_access_at = COALESCE(first_access_at, :now),
               last_access_at  = :now
         WHERE code = :c
    """), {"c": code, "now": now})
    db.commit()
    # recarrega atualizado
    link = db.query(PedidoLink).get(code)
    return link, "ok"