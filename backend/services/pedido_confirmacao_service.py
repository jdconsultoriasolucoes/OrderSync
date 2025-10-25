from sqlalchemy.orm import Session
from fastapi import HTTPException
from services.email_service import enviar_email_notificacao, gerar_pdf_pedido_bytes
from services.pdf_service import gerar_pdf_pedido
from models.pedido import Pedido
from models.cliente import ClienteModel
from models.pedido_item import PedidoItem

def processar_confirmacao_pedido(db: Session, pedido_id: int):
    """
    1. Carrega pedido
    2. Marca como CONFIRMADO
    3. Gera PDF (BytesIO)
    4. Dispara e-mail com anexo
    """
    # 1) pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # 2) status
    pedido.status = "CONFIRMADO"
    # ex.: pedido.confirmado_em = datetime.utcnow()
    db.commit()
    db.refresh(pedido)

    # carregar itens e cliente (ajuste para seu schema)
    itens = db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).all()
    cliente = None
    try:
        # se você salva codigo_cliente no pedido
        if hasattr(pedido, "codigo_cliente"):
            cliente = db.query(ClienteModel).filter(ClienteModel.codigo == pedido.codigo_cliente).first()
    except Exception:
        cliente = None

    # 3) PDF em memória
    pdf_bytes = gerar_pdf_pedido_bytes(pedido, itens, cliente)

    # 4) e-mail com anexo
    enviar_email_notificacao(db, pedido, link_pdf=None, pdf_bytes=pdf_bytes)

    return {"ok": True, "pedido_id": pedido.id}