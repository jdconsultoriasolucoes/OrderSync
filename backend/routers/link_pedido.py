from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from services.link_pedido import gerar_link_code, resolver_code
from models.pedido_link import PedidoLink
from pathlib import Path
from datetime import datetime
from sqlalchemy import update
from fastapi import Depends
from core.deps import get_current_user
from models.usuario import UsuarioModel

router = APIRouter(prefix="/link_pedido", tags=["Link Pedido"])

PEDIDO_HTML = Path("/opt/render/project/src/frontend/public/tabela_preco/pedido_cliente.html")

@router.post("/gerar")
def gerar_link(body: dict, request: Request, current_user: UsuarioModel = Depends(get_current_user)):
    # abre sessão local (sem Depends)
    with SessionLocal() as db:
        tabela_id = int(body["tabela_id"])
        com_frete = bool(body["com_frete"])
        codigo_cliente = body.get("codigo_cliente")
        code, expires_at, data_prevista = gerar_link_code(db, tabela_id, com_frete, body.get("data_prevista"), body.get("codigo_cliente"))

    # monta URL pública
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    origin = f"{scheme}://{host}"
    url = f"{origin}/p/{code}"

    with SessionLocal() as db:
        db.execute(
            update(PedidoLink)
            .where(PedidoLink.code == code)
            .values(link_url=url, criado_por=current_user.email)
        )
        db.commit()


    return {
        "url": url,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "data_prevista": data_prevista.isoformat() if data_prevista else None,
    }

@router.get("/resolver")
def resolver_link(code: str):
    with SessionLocal() as db:
        link, status = resolver_code(db, code)
        if status == "not_found":
            raise HTTPException(status_code=404, detail="Link não encontrado")
        if status == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

        return {
            "tabela_id": link.tabela_id,
            "com_frete": link.com_frete,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "data_prevista": link.data_prevista.isoformat() if getattr(link, "data_prevista", None) else None,
            "codigo_cliente": getattr(link, "codigo_cliente", None),
            "uses": getattr(link, "uses", None),
            "first_access_at": getattr(link, "first_access_at", None) and link.first_access_at.isoformat(),
            "last_access_at": getattr(link, "last_access_at", None) and link.last_access_at.isoformat(),
            "created_at": getattr(link, "created_at", None) and link.created_at.isoformat(),
            "link_url": getattr(link, "link_url", None),
        }

# Rota curta que serve o HTML público
router_short = APIRouter()

@router_short.get("/p/{code}")
def abrir_link(code: str):
    if not PEDIDO_HTML.exists():
        raise HTTPException(500, "Arquivo pedido_cliente.html não encontrado")
    return FileResponse(PEDIDO_HTML, headers={
        "X-Robots-Tag": "noindex, nofollow",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    })