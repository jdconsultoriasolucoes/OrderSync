from sqlalchemy.orm import Session
from services.email_service import enviar_email_notificacao

def processar_confirmacao_pedido(db: Session, pedido_id: int):
    """
    1. Carrega pedido
    2. Marca como CONFIRMADO
    3. Gera PDF
    4. Sobe PDF pro Drive e pega link_pdf
    5. Dispara e-mail
    """
    # 1. carregar pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # 2. atualizar status
    pedido.status = "CONFIRMADO"
    # exemplo: pedido.confirmado_em = datetime.utcnow()
    db.commit()
    db.refresh(pedido)

    # 3. gerar PDF  (TODO: chamar sua função atual de geração)
    # link_pdf = gerar_pdf_e_subir_drive(pedido)
    link_pdf = "LINK_DO_DRIVE_AQUI"  # placeholder

    # 4. enviar e-mail usando configs
    enviar_email_notificacao(db, pedido, link_pdf)

    return pedido
