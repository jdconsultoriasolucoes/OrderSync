# backend/services/email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
import ssl, smtplib
from sqlalchemy.orm import Session

# ===== IMPORTS CORRETOS =====
try:
    from models.cliente_v2 import ClienteModelV2       # <- Atualizado para V2
except ModuleNotFoundError:
    from cliente_v2 import ClienteModelV2

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
# Busca e-mail do cliente (usa codigo_cliente como ID do V2)
# ------------------------
def get_email_cliente_responsavel_compras(db: Session, codigo_cliente) -> Optional[str]:
    if not codigo_cliente:
        return None
    
    # Tenta converter para int, pois IDs são inteiros/bigint
    try:
        c_id = int(codigo_cliente)
    except (ValueError, TypeError):
        return None

    row = (
        db.query(ClienteModelV2.compras_email_resposavel)
        .filter(ClienteModelV2.id == c_id)
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
    # destinatários internos (separados por vírgula) — compatível com sua tela
    destinatarios = []
    if getattr(cfg_msg, "destinatario_interno", None):
        destinatarios = [e.strip() for e in cfg_msg.destinatario_interno.split(",") if e.strip()]

    # cópia opcional para o cliente responsável compras (controlada pela flag da mensagem)
    cc = []
    if getattr(cfg_msg, "enviar_para_cliente", False):
        email_cli = get_email_cliente_responsavel_compras(
            db,
            getattr(pedido, "codigo_cliente", None)  # deve casar com codigo_cliente do Cliente
        )
        if email_cli:
            cc.append(email_cli)

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
    base_subject = assunto or "Pedido confirmado"
    if pedido_info.get("pedido_id"):
        msg["Subject"] = f"{base_subject} #{pedido_info['pedido_id']}"
    else:
        msg["Subject"] = base_subject
    
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
        # Envia para destinatários internos
        server.sendmail(remetente, to_all, msg.as_string())
        
        # ---------------------------------------------------------
        # Envio Opcional para o Cliente (PDF sem validade)
        # ---------------------------------------------------------
        if cfg_msg.enviar_para_cliente and getattr(pedido, "cliente_email", None):
            try:
                from services.pdf_service import gerar_pdf_pedido
                pdf_cliente_bytes = gerar_pdf_pedido(pedido, sem_validade=True)
                
                msg_cliente = MIMEMultipart()
                msg_cliente["From"] = remetente
                msg_cliente["To"] = pedido.cliente_email
                msg_cliente["Subject"] = f"Confirmação de Pedido #{pedido.id} - {pedido.cliente_nome}"
                
                # Corpo simples para o cliente
                body_client = f"""\
Prezado(a) {pedido.cliente_nome},

Seu pedido #{pedido.id} foi confirmado com sucesso.
Segue em anexo a cópia do pedido.

Atenciosamente,
Equipe OrderSync
"""
                msg_cliente.attach(MIMEText(body_client, "plain"))
                
                # Anexo (usando MIMEApplication para evitar erro de encoding)
                part_c = MIMEApplication(pdf_cliente_bytes, _subtype="pdf")
                part_c.add_header(
                    "Content-Disposition", 
                    "attachment", 
                    filename=f"Pedido_{pedido.id}.pdf"
                )
                msg_cliente.attach(part_c)
                
                server.sendmail(remetente, [pedido.cliente_email], msg_cliente.as_string())
                print(f"Email enviado para cliente: {pedido.cliente_email}")
                
            except Exception as e:
                print(f"Erro ao enviar email para cliente: {e}")

        server.quit()


def enviar_email_recuperacao_senha(db: Session, email_destino: str, link_reset: str) -> None:
    """
    Envia e-mail com link de recuperação de senha.
    """
    cfg_smtp = _get_cfg_smtp(db)
    remetente = (getattr(cfg_smtp, "remetente_email", "") or getattr(cfg_smtp, "smtp_user", "")).strip()
    
    assunto = "Recuperação de Senha - OrderSync"
    
    corpo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
            <h2 style="color: #2563eb;">Recuperação de Senha</h2>
            <p>Você solicitou a redefinição de sua senha no OrderSync.</p>
            <p>Clique no botão abaixo para criar uma nova senha:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{link_reset}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Redefinir Minha Senha</a>
            </p>
            <p>Se o botão não funcionar, copie e cole o link abaixo no seu navegador:</p>
            <p style="font-size: 12px; color: #666; word-break: break-all;">{link_reset}</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #999;">Este link é válido por 15 minutos. Se você não solicitou isso, ignore este e-mail.</p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["From"] = remetente
    msg["To"] = email_destino
    msg["Subject"] = assunto
    
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))
    
    try:
        with _abrir_conexao(cfg_smtp) as server:
            server.sendmail(remetente, [email_destino], msg.as_string())
            print(f"Email de recuperação enviado para: {email_destino}")
    except Exception as e:
        print(f"Erro ao enviar email de recuperação: {e}")
        # Não lançar exceção para não expor erro ao usuário (security by obscurity, ou melhor, UX)
        # Mas logar é importante.
