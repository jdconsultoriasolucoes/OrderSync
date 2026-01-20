from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text # inserted
from database import SessionLocal
from services.link_pedido import gerar_link_code, resolver_code
from models.pedido_link import PedidoLink
from pathlib import Path
from datetime import datetime
from sqlalchemy import update

from core.deps import get_current_user
from models.usuario import UsuarioModel

router = APIRouter(prefix="/link_pedido", tags=["Link Pedido"])

# Resolve relative path to frontend/public/tabela_preco/pedido_cliente.html
# Assumes structure: root/backend/routers/link_pedido.py -> root/frontend/...
BASE_DIR = Path(__file__).resolve().parents[2] 
PEDIDO_HTML = BASE_DIR / "frontend" / "public" / "tabela_preco" / "pedido_cliente.html"

if not PEDIDO_HTML.exists():
    # Fallback/Debug log if needed, or rely on runtime check
    pass

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
             return {
                "is_expired": True,
                "link_status": "EXPIRADO",
                # Now we return actual data so user can see what it was
                "tabela_id": link.tabela_id,
                "com_frete": link.com_frete,
                "expires_at": link.expires_at.isoformat() if link.expires_at else None,
                "data_prevista": link.data_prevista.isoformat() if getattr(link, "data_prevista", None) else None,
                "codigo_cliente": getattr(link, "codigo_cliente", None),
                "link_url": getattr(link, "link_url", None)
             }

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
            "is_expired": False,
            "link_status": getattr(link, "link_status", "ABERTO")
        }

# Rota curta que serve o HTML público
router_short = APIRouter()

@router_short.get("/p/{code}")
def abrir_link(code: str):
    if not PEDIDO_HTML.exists():
        raise HTTPException(500, "Arquivo pedido_cliente.html não encontrado")
@router.get("/lista_preco/{code}")
def baixar_lista_preco(code: str):
    from services.pdf_service import gerar_pdf_lista_preco
    
    with SessionLocal() as db:
        # Resolve o link
        link, status = resolver_code(db, code)
        if status == "not_found":
            raise HTTPException(404, "Link não encontrado")
        
        # Recupera o pedido associado a este link?
        # Links de pedido geralmente não têm um id_pedido direto se forem links de TABELA DE PREÇO (Gerar Link).
        # Se for link de "Visualizar Pedido" (já criado)?
        # Pelo código `gerar_link_code`, o link é amarrado a `tabela_id`.
        # Mas `gerar_pdf_lista_preco` espera um objeto `PedidoPdf`.
        # Precisamos simular um objeto PedidoPdf baseado na Tabela de Preço, sem ser um pedido real.
        # Ou... o usuário salva um orçamento?
        # O pedido_preview retorna JSON.
        # Precisamos de algo como `carregar_pedido_preview_como_pdf`.
        
        # Vamos criar um helper rápido aqui ou em services para converter Tabela -> PedidoPdfFake
        
        # Como o user quer "gerar esse arquivo em pdf para ser enviado ao cliente como se fosse o link de orçamento",
        # assumimos que ele quer os ITENS da Tabela, mas formatados.
        
        tabela_id = link.tabela_id
        
        # Busca itens da tabela
        sql = text("""
            SELECT 
                t.*,
                c.nome_fantasia
            FROM tb_tabela_preco t
            LEFT JOIN t_cadastro_cliente c ON c.codigo::text = t.codigo_cliente
            WHERE t.id_tabela = :tid AND t.ativo IS TRUE
        """)
        rows = db.execute(sql, {"tid": tabela_id}).mappings().all()
        
        if not rows:
             raise HTTPException(404, "Tabela vazia ou não encontrada")
             
        # Monta Fake PedidoPdf
        from models.pedido_pdf import PedidoPdf, PedidoPdfItem
        
        head = rows[0]
        itens = []
        for r in rows:
            itens.append(PedidoPdfItem(
                codigo=r.get("codigo_produto_supra"),
                produto=r.get("descricao_produto"),
                embalagem=r.get("embalagem"),
                quantidade=0, # Lista de preço nao tem qtd definida
                condicao_pagamento=r.get("codigo_plano_pagamento"), # ou descricao
                tabela_comissao=None,
                valor_retira=float(r.get("valor_s_frete") or 0),
                valor_entrega=float(r.get("valor_frete") or 0)
            ))
            
        fake_pedido = PedidoPdf(
            id_pedido=0,
            codigo_cliente=head.get("codigo_cliente"),
            cliente=head.get("cliente"),
            nome_fantasia=head.get("nome_fantasia"),
            data_pedido=head.get("criado_em") or datetime.now(),
            data_entrega_ou_retirada=None,
            frete_total=0.0,
            frete_kg=float(head.get("frete_kg") or 0),
            validade_tabela="Ver tabela",
            total_peso_bruto=0.0,
            total_peso_liquido=0.0,
            total_valor=0.0,
            observacoes="Lista de Preços gerada via sistema.",
            itens=itens
        )
        
        pdf_bytes = gerar_pdf_lista_preco(fake_pedido)
        
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=lista_precos_{code}.pdf"
        })