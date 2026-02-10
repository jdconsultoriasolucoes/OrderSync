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
    
    # Busca pela string do código empresarial (cadastro_codigo_da_empresa)
    s_cod = str(codigo_cliente).strip()

    row = (
        db.query(
            ClienteModelV2.compras_email_resposavel,
            ClienteModelV2.faturamento_email_danfe,
            ClienteModelV2.recebimento_email,
            ClienteModelV2.cobranca_resp_email,
            ClienteModelV2.legal_email
        )
        .filter(ClienteModelV2.cadastro_codigo_da_empresa == s_cod)
        .first()
    )
    
    if not row:
        print(f"DEBUG: Cliente '{s_cod}' não encontrado para busca de e-mail.")
        return None
        
    # Prioridade de emails
    emails = [
        row.compras_email_resposavel,
        row.faturamento_email_danfe,
        row.recebimento_email,
        row.cobranca_resp_email,
        row.legal_email
    ]
    
    # Retorna o primeiro que não for vazio
    for e in emails:
        if e and str(e).strip():
            print(f"DEBUG: Email encontrado para cliente '{s_cod}': {str(e).strip()}")
            return str(e).strip()
            
    return None
        
    # Prioridade de emails
    emails = [
        row.compras_email_resposavel,
        row.faturamento_email_danfe,
        row.recebimento_email,
        row.cobranca_resp_email,
        row.legal_email
    ]
    
    # Retorna o primeiro que não for vazio
    for e in emails:
        if e and str(e).strip():
            return str(e).strip()
            
    return None


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
    pdf_bytes: Optional[bytes] = None,
    pdf_bytes_cliente: Optional[bytes] = None
) -> None:
    cfg_smtp = _get_cfg_smtp(db)
    cfg_msg  = _get_cfg_msg(db)

    remetente = (getattr(cfg_smtp, "remetente_email", "") or getattr(cfg_smtp, "smtp_user", "")).strip()

    # 1. Identificar Destinatários Internos
    destinatarios_internos = []
    if getattr(cfg_msg, "destinatario_interno", None):
        destinatarios_internos = [e.strip() for e in cfg_msg.destinatario_interno.split(",") if e.strip()]
    
    # 2. Identificar Email Cliente
    email_cliente = None
    if getattr(cfg_msg, "enviar_para_cliente", False):
        # Tenta usar o email que veio no pedido (ex: do cadastro V1 ou digitado na hora)
        email_pedido = getattr(pedido, "cliente_email", None)
        
        # Se não tiver, tenta buscar pelo código no cadastro V2
        email_v2 = None
        if not email_pedido:
             c_temp = getattr(pedido, "codigo_cliente", None)
             email_v2 = get_email_cliente_responsavel_compras(db, c_temp)

        email_cliente = email_pedido or email_v2
        
    pedido_info = {
        "pedido_id": getattr(pedido, "id", ""),
        "cliente_nome": getattr(pedido, "cliente_nome", "") or getattr(pedido, "nome_cliente", ""),
        "total_pedido": getattr(pedido, "total_pedido", ""),
    }

    # =========================================================================
    # ENVIO 1: INTERNO (Para a equipe de vendas)
    # =========================================================================
    if destinatarios_internos:
        try:
            assunto    = render_placeholders(getattr(cfg_msg, "assunto_padrao", "") or "", pedido_info, link_pdf)
            corpo_html = render_placeholders(getattr(cfg_msg, "corpo_html", "") or "", pedido_info, link_pdf)
            
            msg = MIMEMultipart("mixed")
            msg["From"] = remetente
            msg["To"]   = ", ".join(destinatarios_internos)
            
            base_subject = assunto or "Novo Pedido (Interno)"
            if pedido_info.get("pedido_id"):
                msg["Subject"] = f"{base_subject}" # O placeholder já deve cuidar do ID se configurado
            else:
                msg["Subject"] = base_subject

            alt = MIMEMultipart("alternative")
            if corpo_html:
                alt.attach(MIMEText(corpo_html, "html", "utf-8"))
            else:
                alt.attach(MIMEText("Novo pedido recebido.", "plain", "utf-8"))
            msg.attach(alt)

            # Anexo: PDF Vendedor (Completo) - usa pdf_bytes
            if pdf_bytes:
                part = MIMEApplication(pdf_bytes, _subtype="pdf")
                filename = f"Pedido_{pedido_info['pedido_id']}_Interno.pdf"
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)

            with _abrir_conexao(cfg_smtp) as server:
                server.sendmail(remetente, destinatarios_internos, msg.as_string())
                print(f"Email Interno enviado para: {destinatarios_internos}")
        
        except Exception as e:
            print(f"Erro ao enviar email interno: {e}")
            # Não aborta, tenta enviar o do cliente

    # =========================================================================
    # ENVIO 2: CLIENTE (Se habilitado e tiver email)
    # =========================================================================
    if email_cliente:
        try:
            # Usa campos específicos de cliente ou fallback para o padrão se vazio (opcional, mas melhor não)
            assunto_cli = getattr(cfg_msg, "assunto_cliente", "") or "Confirmação de Pedido"
            corpo_cli   = getattr(cfg_msg, "corpo_html_cliente", "") or "<p>Seu pedido foi recebido.</p>"
            
            assunto    = render_placeholders(assunto_cli, pedido_info, link_pdf)
            corpo_html = render_placeholders(corpo_cli, pedido_info, link_pdf)
            
            msg = MIMEMultipart("mixed")
            msg["From"] = remetente
            msg["To"]   = email_cliente
            msg["Subject"] = assunto

            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(corpo_html, "html", "utf-8"))
            msg.attach(alt)

            # Anexo: PDF Cliente (Simplificado) - usa pdf_bytes_cliente
            # Se não vier o específico, usa o pdf_bytes (fallback? melhor não, user pediu diferente)
            anexo_bytes = pdf_bytes_cliente if pdf_bytes_cliente else pdf_bytes
            
            if anexo_bytes:
                part = MIMEApplication(anexo_bytes, _subtype="pdf")
                filename = f"Orcamento_{pedido_info['pedido_id']}.pdf"
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)

            with _abrir_conexao(cfg_smtp) as server:
                server.sendmail(remetente, [email_cliente], msg.as_string())
                print(f"Email Cliente enviado para: {email_cliente}")

        except Exception as e:
            print(f"Erro ao enviar email cliente: {e}")
            raise e # Relança para o caller saber que falhou pelo menos um envio importante


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
