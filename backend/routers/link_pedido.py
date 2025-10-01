from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import get_db
from services.link_pedido import gerar_link_code, resolver_code
from models.pedido_link import PedidoLink
from pathlib import Path

router = APIRouter(prefix="/link_pedido", tags=["Link Pedido"])

PEDIDO_HTML = Path("/opt/render/project/src/frontend/public/tabela_preco/pedido_cliente.html")

@router.post("/gerar")
def gerar_link(body: dict, request: Request, db: Session = Depends(get_db)):
    tabela_id = int(body["tabela_id"])
    com_frete = bool(body["com_frete"])
    code, expires_at = gerar_link_code(db, tabela_id, com_frete)

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.hostname)
    origin = f"{scheme}://{host}"
    url = f"{origin}/p/{code}"

    return {"url": url, "expires_at": expires_at}

@router.get("/resolver")
def resolver(code: str, db: Session = Depends(get_db)):
    link, status = resolver_code(db, code)
    if status == "not_found":
        raise HTTPException(404, "Link não encontrado")
    if status == "expired":
        raise HTTPException(410, "Link expirado")
    return {"tabela_id": link.tabela_id, "com_frete": link.com_frete}

router_short = APIRouter()

@router_short.get("/p/{code}")
def abrir_link(code: str):
    if not PEDIDO_HTML.exists():
        raise HTTPException(500, "Arquivo pedido_cliente.html não encontrado")
    # Cabeçalhos úteis (opcional)
    return FileResponse(PEDIDO_HTML, headers={
        "X-Robots-Tag": "noindex, nofollow",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    })
