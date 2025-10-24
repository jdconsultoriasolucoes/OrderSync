from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models.config_email_mensagem import ConfigEmailMensagem
from models.config_email_smtp import ConfigEmailSMTP
from cliente import ClienteModel  # seu modelo ORM real de cliente


def get_cfg_mensagem(db: Session) -> ConfigEmailMensagem:
    cfg = (
        db.query(ConfigEmailMensagem)
        .filter(ConfigEmailMensagem.id == 1)
        .first()
    )
    if not cfg:
        raise HTTPException(
            status_code=500,
            detail="Configuração de mensagem de e-mail (config_email_mensagem.id=1) não encontrada."
        )
    return cfg


def get_cfg_smtp(db: Session) -> ConfigEmailSMTP:
    cfg = (
        db.query(ConfigEmailSMTP)
        .filter(ConfigEmailSMTP.id == 1)
        .first()
    )
    if not cfg:
        raise HTTPException(
            status_code=500,
            detail="Configuração SMTP (config_email_smtp.id=1) não encontrada."
        )
    return cfg


def get_email_cliente_responsavel_compras(
    db: Session,
    codigo_cliente: Optional[str]
) -> Optional[str]:
    """
    Retorna o email do responsável de compras do cliente correspondente ao código.
    Usa a própria tabela tb_cadastro_cliente via ClienteModel.
    """
    if not codigo_cliente:
        return None

    row = (
        db.query(ClienteModel.email_responsavel_compras)
        .filter(ClienteModel.codigo_da_empresa == codigo_cliente)
        .first()
    )

    if not row:
        return None

    # row é um tuple-like com só a coluna, então:
    email_cli = row[0]
    if email_cli and email_cli.strip():
        return email_cli.strip()
    return None


def montar_destinatarios(
    cfg_msg: ConfigEmailMensagem,
    email_cliente: Optional[str]
) -> List[str]:
    """
    - Sempre inclui destinatario_interno
    - Se enviar_para_cliente=True e email_cliente existe, inclui o cliente
    - Remove duplicados e vazios
    """
    to_list: List[str] = []

    # 1) internos
    internos_raw = cfg_msg.destinatario_interno.split(",")
    internos = [e.strip() for e in internos_raw if e.strip()]
    to_list.extend(internos)

    # 2) cliente, se flag ligada
    if cfg_msg.enviar_para_cliente and email_cliente:
        to_list.append(email_cliente)

    # dedup
    final_list: List[str] = []
    for addr in to_list:
        if addr not in final_list:
            final_list.append(addr)

    return final_list


def render_placeholders(
    template_str: str,
    pedido_info: dict,
    link_pdf: Optional[str]
) -> str:
    """
    Placeholder simples baseado no que você já salva em tb_pedidos:
      {{pedido_id}}
      {{cliente_nome}}
      {{total_pedido}}
      {{link_pdf}}
    """
    out = template_str or ""
    mapping = {
        "{{pedido_id}}":    str(pedido_info.get("pedido_id", "")),
        "{{cliente_nome}}": str(pedido_info.get("cliente_nome", "")),
        "{{total_pedido}}": str(pedido_info.get("total_pedido", "")),
        "{{link_pdf}}":     (link_pdf or ""),
    }
    for k, v in mapping.items():
        out = out.replace(k, v)
    return out


def enviar_email_notificacao(
    db: Session,
    pedido_info: dict,
    codigo_cliente: Optional[str],
    link_pdf: Optional[str]
):
    """
    Envia o e-mail final após confirmar pedido.
    pedido_info precisa ter no mínimo:
      {
        "pedido_id": new_id,
        "cliente_nome": <string>,
        "total_pedido": <float>
      }
    """

    cfg_msg = get_cfg_mensagem(db)
    cfg_smtp = get_cfg_smtp(db)

    if cfg_msg.enviar_para_cliente:
        email_cli = get_email_cliente_responsavel_compras(db, codigo_cliente)
    else:
        email_cli = None

    destinatarios = montar_destinatarios(cfg_msg, email_cli)
    if not destinatarios:
        raise HTTPException(status_code=500, detail="Nenhum destinatário para envio de pedido confirmado.")

    assunto_final = render_placeholders(cfg_msg.assunto_padrao, pedido_info, link_pdf)
    corpo_final_html = render_placeholders(cfg_msg.corpo_html, pedido_info, link_pdf)

    # Monta MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto_final
    msg["From"] = cfg_smtp.remetente_email
    msg["To"] = ", ".join(destinatarios)

    part_html = MIMEText(corpo_final_html, "html")
    msg.attach(part_html)

    # SMTP
    try:
        if cfg_smtp.usar_tls:
            server = smtplib.SMTP(cfg_smtp.smtp_host, cfg_smtp.smtp_port)
            server.starttls()
        else:
            # conexão SSL direta (porta 465 por ex.)
            server = smtplib.SMTP_SSL(cfg_smtp.smtp_host, cfg_smtp.smtp_port)

        server.login(cfg_smtp.smtp_user, cfg_smtp.smtp_senha)
        server.sendmail(cfg_smtp.remetente_email, destinatarios, msg.as_string())
        server.quit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar e-mail: {e}")
