import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy.orm import Session

from models.cliente import ClienteModel
from models.config_email import ConfigEmailSMTPModel, ConfigEmailMensagemModel

# ------------------------
# Helpers de placeholder
# ------------------------
def render_placeholders(template: str, pedido_info: dict, link_pdf: Optional[str] = None) -> str:
    if not template:
        return ""
    s = template
    s = s.replace("{{pedido_id}}", str(pedido_info.get("pedido_id", "") or ""))
    s = s.replace("{{cliente_nome}}", str(pedido_info.get("cliente_nome", "") or ""))
    s = s.replace("{{total_pedido}}", str(pedido_info.get("total_pedido", "") or ""))
    s = s.replace("{{link_pdf}}", str(link_pdf or ""))
    return s

# ------------------------
# Busca e-mail do cliente
# ------------------------
def get_email_cliente_responsavel_compras(db: Session, codigo_cliente: Optional[str]) -> Optional[str]:
    if not codigo_cliente:
        return None
    # ATENÇÃO: alinhe o campo abaixo com o seu schema real
    row = (
        db.query(ClienteModel.email_responsavel_compras)
        .filter(ClienteModel.codigo == codigo_cliente)  # <- use .codigo se este for o campo chave
        .first()
    )
    return row[0] if row and row[0] else None

# ------------------------
# Carrega configs
# ------------------------
def _get_cfg_smtp(db: Session) -> ConfigEmailSMTPModel:
    cfg = db.query(ConfigEmailSMTPModel).first()
    if not cfg:
        raise RuntimeError("Config SMTP não encontrada")
    return cfg

def _get_cfg_msg(db: Session) -> ConfigEmailMensagemModel:
    cfg = db.query(ConfigEmailMensagemModel).first()
    if not cfg:
        raise RuntimeError("Config de mensagem de e-mail não encontrada")
    return cfg

# ------------------------
# Envio
# ------------------------
def _abrir_conexao(cfg_smtp: ConfigEmailSMTPModel) -> smtplib.SMTP:
    host = cfg_smtp.smtp_host
    port = cfg_smtp.smtp_port
    user = cfg_smtp.smtp_user
    pwd = cfg_smtp.smtp_password

    if cfg_smtp.usar_tls:
        server = smtplib.SMTP(host, port, timeout=20)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        # Porta típica 465
        server = smtplib.SMTP_SSL(host, port, timeout=20)

    if user:
        server.login(user, pwd or "")
    return server

def enviar_email_notificacao(
    db: Session,
    pedido,
    link_pdf: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None
) -> None:
    cfg_smtp = _get_cfg_smtp(db)
    cfg_msg = _get_cfg_msg(db)

    # From obrigatório: alguns provedores exigem que seja igual ao usuário autenticado
    remetente = cfg_smtp.email_origem or cfg_smtp.smtp_user

    # To (lista de colaboradores que recebem a separação)
    # Se você já guarda lista na config, use-a; caso não, monte aqui.
    # Exemplo: cfg_msg.destinatarios_padrao (string separada por vírgulas)
    destinatarios = []
    if getattr(cfg_msg, "destinatarios_padrao", None):
        destinatarios = [e.strip() for e in cfg_msg.destinatarios_padrao.split(",") if e.strip()]

    # Opcional: add e-mail do cliente responsável compras em Cc
    email_cli = get_email_cliente_responsavel_compras(
        db,
        getattr(pedido, "codigo_cliente", None)
    )
    cc = [email_cli] if email_cli else []

    pedido_info = {
        "pedido_id": getattr(pedido, "id", ""),
        "cliente_nome": getattr(pedido, "cliente_nome", "") or getattr(pedido, "nome_cliente", ""),
        "total_pedido": getattr(pedido, "total_pedido", ""),
    }

    assunto = render_placeholders(cfg_msg.assunto_padrao or "", pedido_info, link_pdf)
    corpo_html = render_placeholders(cfg_msg.corpo_html or "", pedido_info, link_pdf)
    corpo_txt = render_placeholders(cfg_msg.corpo_texto or "", pedido_info, link_pdf)

    msg = MIMEMultipart("mixed")
    msg["From"] = remetente
    msg["To"] = ", ".join(destinatarios) if destinatarios else remetente
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = assunto or f"Pedido #{pedido_info['pedido_id']} confirmado"

    # Alternativas: texto + html
    alt = MIMEMultipart("alternative")
    if corpo_txt:
        alt.attach(MIMEText(corpo_txt, "plain", "utf-8"))
    if corpo_html:
        alt.attach(MIMEText(corpo_html, "html", "utf-8"))
    msg.attach(alt)

    # Anexo PDF se fornecido
    if pdf_bytes:
        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        filename = f"pedido_{pedido_info['pedido_id']}.pdf"
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    # Conexão e envio
    to_all = destinatarios + cc if cc else destinatarios
    if not to_all:
        # fallback: manda para o remetente para não perder o evento
        to_all = [remetente]

    with _abrir_conexao(cfg_smtp) as server:
        server.sendmail(remetente, to_all, msg.as_string())