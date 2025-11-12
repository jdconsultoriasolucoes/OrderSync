# backend/services/email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from typing import Optional
import ssl, smtplib
from sqlalchemy.orm import Session

# ===== IMPORTS CORRETOS =====
try:
    from models.cliente import ClienteModel            # <- sua classe real
except ModuleNotFoundError:
    from cliente import ClienteModel                   # fallback se não houver pacote models

try:
    from models.config_email_mensagem import ConfigEmailMensagem as ConfigEmailMensagemModel
    from models.config_email_smtp import ConfigEmailSMTP as ConfigEmailSMTPModel
except ModuleNotFoundError:
    from config_email_mensagem import ConfigEmailMensagem as ConfigEmailMensagemModel
    from config_email_smtp import ConfigEmailSMTP as ConfigEmailSMTPModel


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
# Busca e-mail do cliente (usa codigo_da_empresa do seu modelo)
# ------------------------
def get_email_cliente_responsavel_compras(db: Session, codigo_cliente) -> Optional[str]:
    if not codigo_cliente:
        return None
    row = (
        db.query(ClienteModel.email_responsavel_compras)
        .filter(ClienteModel.codigo_da_empresa == codigo_cliente)  # <- campo correto do seu modelo
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
# Conexão SMTP
# ------------------------
def _abrir_conexao(cfg_smtp):
    host = cfg_smtp.smtp_host.strip()
    port = int(cfg_smtp.smtp_port)
    user = (cfg_smtp.smtp_user or "").strip()
    pwd  = cfg_smtp.smtp_senha or ""
    usar_tls = bool(getattr(cfg_smtp, "usar_tls", True))

    ctx = ssl.create_default_context()
    if usar_tls:
        server = smtplib.SMTP(host, port, timeout=20)
        server.ehlo()
        server.starttls(context=ctx)  # <- sem server_hostname
        server.ehlo()
    else:
        server = smtplib.SMTP_SSL(host, port, timeout=20, context=ctx)
        server.ehlo()

    if user:
        server.login(user, pwd)
    return server

# ------------------------
# Envio
# ------------------------
def enviar_email_notificacao(
    db: Session,
    pedido,
    link_pdf: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None
) -> None:
    cfg_smtp = _get_cfg_smtp(db)
    cfg_msg  = _get_cfg_msg(db)

    remetente = (getattr(cfg_smtp, "remetente_email", "") or getattr(cfg_smtp, "smtp_user", "")).strip()

    # destinatários internos (separados por vírgula) — compatível com sua tela
    destinatarios = []
    if getattr(cfg_msg, "destinatario_interno", None):
        destinatarios = [e.strip() for e in cfg_msg.destinatario_interno.split(",") if e.strip()]

    # cópia opcional para o cliente responsável compras
    email_cli = get_email_cliente_responsavel_compras(
        db,
        getattr(pedido, "codigo_cliente", None)  # deve casar com codigo_da_empresa do Cliente
    )
    cc = [email_cli] if email_cli else []

    pedido_info = {
        "pedido_id": getattr(pedido, "id", ""),
        "cliente_nome": getattr(pedido, "cliente_nome", "") or getattr(pedido, "nome_cliente", ""),
        "total_pedido": getattr(pedido, "total_pedido", ""),
    }

    assunto    = render_placeholders(getattr(cfg_msg, "assunto_padrao", "") or "", pedido_info, link_pdf)
    corpo_html = render_placeholders(getattr(cfg_msg, "corpo_html", "") or "", pedido_info, link_pdf)
    corpo_txt  = ""  # opcional: adicione um campo texto na config se quiser

    msg = MIMEMultipart("mixed")
    msg["From"] = remetente
    msg["To"]   = ", ".join(destinatarios) if destinatarios else remetente
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = assunto or f"Pedido #{pedido_info['pedido_id']} confirmado"

    alt = MIMEMultipart("alternative")
    if corpo_txt:
        alt.attach(MIMEText(corpo_txt, "plain", "utf-8"))
    if corpo_html:
        alt.attach(MIMEText(corpo_html, "html", "utf-8"))
    msg.attach(alt)

    if pdf_bytes:
        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        filename = f"pedido_{pedido_info['pedido_id']}.pdf"
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    to_all = destinatarios + cc if cc else destinatarios
    if not to_all:
        to_all = [remetente]  # fallback

    with _abrir_conexao(cfg_smtp) as server:
        server.sendmail(remetente, to_all, msg.as_string())
