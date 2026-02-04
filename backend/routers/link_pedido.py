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
    return FileResponse(PEDIDO_HTML, headers={
        "X-Robots-Tag": "noindex, nofollow",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    })

@router.get("/lista_preco/{code}")
def baixar_lista_preco(code: str, modo: str = "ambos"):
    from services.pdf_service import gerar_pdf_lista_preco
    
    with SessionLocal() as db:
        # Resolve o link
        link, status = resolver_code(db, code)
        if status == "not_found":
            raise HTTPException(404, "Link não encontrado")
            
        # ... [rest of the logic remains same until generation call] ...
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
                valor_entrega=float(r.get("valor_frete") or 0),
                markup=float(r.get("markup") or 0),
                valor_final_markup=float(r.get("valor_final_markup") or 0),
                valor_s_frete_markup=float(r.get("valor_s_frete_markup") or 0)
            ))
            
        # Busca validade global (mesma lógica do router meta/validade_global)
        sql_val = text("SELECT MAX(CAST(validade_tabela AS DATE)) FROM t_cadastro_produto_v2 WHERE status_produto = 'ATIVO'")
        val_db = db.execute(sql_val).scalar()
        validade_fmt = val_db.strftime('%d/%m/%Y') if val_db else "Ver tabela"

        fake_pedido = PedidoPdf(
            id_pedido=0,
            codigo_cliente=head.get("codigo_cliente"),
            cliente=head.get("cliente"),
            nome_fantasia=head.get("nome_fantasia"),
            data_pedido=datetime.now(), # <--- USA DATA ATUAL (Geração)
            data_entrega_ou_retirada=None,
            frete_total=0.0,
            frete_kg=float(head.get("frete_kg") or 0),
            validade_tabela=validade_fmt, # <--- USA VALIDADE CALCULADA
            total_peso_bruto=0.0,
            total_peso_liquido=0.0,
            total_valor=0.0,
            observacoes="Lista de Preços gerada via sistema.",
            itens=itens
        )
        
        # Prepare safe filename
        import re
        raw_cliente = head.get("cliente") or "cliente"
        # Keep alphanumeric, spaces, hyphens, underscores
        safe_cliente = re.sub(r'[^a-zA-Z0-9 \-_]', '', raw_cliente).strip()
        # Avoid multiple spaces
        safe_cliente = re.sub(r'\s+', ' ', safe_cliente)
        
        pdf_bytes = gerar_pdf_lista_preco(fake_pedido, modo_frete=modo)
        
        # Quote filename to handle spaces safely
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="Preco Lista - {safe_cliente}.pdf"'
        })

@router.get("/pdf_cliente/{code}")
def baixar_pdf_cliente(code: str):
    """
    Endpoint dedicado para o cliente baixar o PDF do orçamento (Layout Cliente).
    Busca o pedido associado ao 'link_token' (que é o 'code').
    """
    with SessionLocal() as db:
        # Busca o ID do pedido pelo link_token
        # IMPORTANTE: Só retorna se o status for 'CONFIRMADO' ou 'EM SEPARAÇÃO' etc.
        # Se houver múltiplos (retry?), pega o mais recente? O code deve ser único por tentativa?
        # A rigor, 1 link = 1 pedido (na implementação atual de pedido_confirmacao_service).
        row = db.execute(text("""
            SELECT id_pedido, cliente 
            FROM tb_pedidos 
            WHERE TRIM(link_token) = :c 
            ORDER BY id_pedido DESC 
            LIMIT 1
        """), {"c": code.strip()}).mappings().first()

        if not row:
            # Debug: Mostrar o código que falhou
            print(f"[baixar_pdf_cliente] Falha: Link token '{code}' não encontrado ou pedido não confirmado.")
            raise HTTPException(404, f"Pedido não encontrado para este link ({code}) ou link ainda não confirmado.")
        
        pedido_id = row["id_pedido"]
        cliente_nome = row["cliente"] or "Cliente"

        try:
            from services.pedido_pdf_data import carregar_pedido_pdf
            from services.pdf_service import gerar_pdf_pedido
            
            print(f"[baixar_pdf_cliente] Gerando PDF para pedido_id={pedido_id} (Token: {code})")
            
            # Carrega dados
            pedido_pdf = carregar_pedido_pdf(db, pedido_id)
            
            # Gera PDF com flag sem_validade=True (LAYOUT CLIENTE / ORÇAMENTO)
            pdf_bytes = gerar_pdf_pedido(pedido_pdf, sem_validade=True)
            
            # Nome do arquivo seguro
            import re
            safe_cliente = re.sub(r'[^a-zA-Z0-9 \-_]', '', cliente_nome).strip()
            safe_cliente = re.sub(r'\s+', ' ', safe_cliente)
            filename = f"Orcamento_{pedido_id}_{safe_cliente}.pdf"
            
            return Response(content=pdf_bytes, media_type="application/pdf", headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            })
            
        except Exception as e:
            # Logar erro real no server
            print(f"Erro gerando PDF Cliente: {e}")
            raise HTTPException(500, "Erro ao gerar PDF do pedido.")
