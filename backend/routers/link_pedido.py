from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from services.link_pedido import gerar_link_code, resolver_code
from models.pedido_link import PedidoLink
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/link_pedido", tags=["Link Pedido"])

PEDIDO_HTML = Path("/opt/render/project/src/frontend/public/tabela_preco/pedido_cliente.html")

@router.post("/gerar")
def gerar_link(body: dict, request: Request):
    # abre sessão local (sem Depends)
    with SessionLocal() as db:
        tabela_id = int(body["tabela_id"])
        com_frete = bool(body["com_frete"])
        data_prevista_str = body.get("data_prevista")  # pode ser None

        code, expires_at, data_prevista = gerar_link_code(
            db, tabela_id, com_frete, data_prevista_str
        )

    # monta URL pública
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    origin = f"{scheme}://{host}"
    url = f"{origin}/p/{code}"

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