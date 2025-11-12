# services/pedido_confirmacao_service.py
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from services.pdf_service import gerar_pdf_pedido_bytes
from services.email_service import enviar_email_notificacao
from models.pedido import PedidoModel

def _carregar_pedido(db: Session, pedido_id: int) -> PedidoModel:
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise ValueError(f"Pedido {pedido_id} não encontrado")
    return pedido

def _marcar_confirmado(db: Session, pedido: PedidoModel) -> None:
    pedido.status = "CONFIRMADO"
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

def processar_confirmacao_pedido(db: Session, pedido_id: int) -> Tuple[PedidoModel, Optional[bytes]]:
    """
    1) Carrega pedido
    2) Marca como CONFIRMADO (commit)
    3) Gera PDF em memória
    4) Dispara e-mail (sem derrubar o fluxo se falhar)
    """
    pedido = _carregar_pedido(db, pedido_id)
    _marcar_confirmado(db, pedido)

    pdf_bytes = None
    try:
        pdf_bytes = gerar_pdf_pedido_bytes(db, pedido.id)
    except Exception as e:
        # Logue e siga (PDF é conveniente, não obrigatório)
        print(f"[pdf] falhou: {type(e).__name__}: {e}")

    try:
        enviar_email_notificacao(db, pedido, link_pdf=None, pdf_bytes=pdf_bytes)
    except Exception as e:
        # IMPORTANTÍSSIMO: não derrubar a confirmação do cliente
        print(f"[email] falhou: {type(e).__name__}: {e}")

    return pedido, pdf_bytes
