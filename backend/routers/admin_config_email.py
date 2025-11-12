from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import socket
import ssl
from database import SessionLocal
from models.config_email_mensagem import ConfigEmailMensagem
from models.config_email_smtp import ConfigEmailSMTP
from schemas.config_email import (
    ConfigEmailMensagemOut,
    ConfigEmailMensagemBase,
    ConfigEmailSMTPOut,
    ConfigEmailSMTPUpdate,
)
from typing import Optional, List
from pydantic import BaseModel
import socket, ssl, smtplib, logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

router = APIRouter(
    prefix="/admin/config_email",
    tags=["Admin - Config Email"],
    # IMPORTANTE: aqui precisa de proteção de acesso (auth funcionário)
    # Ex.: dependencies=[Depends(verify_admin_user)]
)
logger = logging.getLogger("ordersync.smtp_test")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
#  ABA 1: Mensagens e Destinatários
# -------------------------

@router.get("/mensagem", response_model=ConfigEmailMensagemOut)
def get_mensagem_cfg(db: Session = Depends(get_db)):
    cfg = (
        db.query(ConfigEmailMensagem)
        .filter(ConfigEmailMensagem.id == 1)
        .first()
    )
    if not cfg:
        # Retorna defaults sem 404 (dia zero não quebra a tela)
        return ConfigEmailMensagemOut(
            id=1,
            destinatario_interno="",
            assunto_padrao="Novo pedido {{pedido_id}}",
            corpo_html="",
            enviar_para_cliente=False,
        )
    return cfg


@router.put("/mensagem", response_model=ConfigEmailMensagemOut)
def update_mensagem_cfg(
    data: ConfigEmailMensagemBase,
    db: Session = Depends(get_db),
):
    cfg = (
        db.query(ConfigEmailMensagem)
        .filter(ConfigEmailMensagem.id == 1)
        .first()
    )

    if not cfg:
        # cria o registro id=1 se ainda não existe
        cfg = ConfigEmailMensagem(
            id=1,
            destinatario_interno=data.destinatario_interno,
            assunto_padrao=data.assunto_padrao,
            corpo_html=data.corpo_html,
            enviar_para_cliente=data.enviar_para_cliente,
        )
        db.add(cfg)
    else:
        cfg.destinatario_interno = data.destinatario_interno
        cfg.assunto_padrao = data.assunto_padrao
        cfg.corpo_html = data.corpo_html
        cfg.enviar_para_cliente = data.enviar_para_cliente

    db.commit()
    db.refresh(cfg)
    return cfg


# -------------------------
#  ABA 2: Remetente e SMTP
# -------------------------

@router.get("/smtp", response_model=ConfigEmailSMTPOut)
def get_smtp_cfg(db: Session = Depends(get_db)):
    cfg = (
        db.query(ConfigEmailSMTP)
        .filter(ConfigEmailSMTP.id == 1)
        .first()
    )
    if not cfg:
        # Defaults seguros para a tela (não envia e-mail com isso — só exibe)
        return ConfigEmailSMTPOut(
            id=1,
            remetente_email="",
            smtp_host="",
            smtp_port=587,
            smtp_user="",
            usar_tls=True,
        )
    return cfg


@router.put("/smtp", response_model=ConfigEmailSMTPOut)
def update_smtp_cfg(
    data: ConfigEmailSMTPUpdate,
    db: Session = Depends(get_db),
):
    data.smtp_host = (data.smtp_host or "").strip()
    data.smtp_user = (data.smtp_user or "").strip()
    if data.remetente_email is not None:
        data.remetente_email = data.remetente_email.strip()

    # sanitize senha: remove quaisquer espaços (senha de app do Gmail às vezes vem com espaços na cópia)
    if data.smtp_senha is not None and data.smtp_senha != "":
        data.smtp_senha = "".join(data.smtp_senha.split())
    cfg = (
        db.query(ConfigEmailSMTP)
        .filter(ConfigEmailSMTP.id == 1)
        .first()
    )

    if not cfg:
        cfg = ConfigEmailSMTP(
            id=1,
            remetente_email=data.remetente_email,
            smtp_host=data.smtp_host,
            smtp_port=data.smtp_port,
            smtp_user=data.smtp_user,
            smtp_senha=(data.smtp_senha or ""),  # inicia a senha
            usar_tls=data.usar_tls,
        )
        db.add(cfg)
    else:
        cfg.remetente_email = data.remetente_email
        cfg.smtp_host = data.smtp_host
        cfg.smtp_port = data.smtp_port
        cfg.smtp_user = data.smtp_user
        if data.smtp_senha:  # só troca se veio algo
            cfg.smtp_senha = data.smtp_senha
        cfg.usar_tls = data.usar_tls

    db.commit()
    db.refresh(cfg)
    return cfg


# ===== Testar CONEXÃO SMTP =====
class TesteSMTPIn(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_senha: Optional[str] = None
    usar_tls: Optional[bool] = None  # se None, vamos inferir pela porta

def testar_smtp_conexao(request: Request):
    db = _get_db_from_request(request)
    # ajuste os imports para seus modelos reais
    from models.config_email_smtp import ConfigEmailSMTP
    cfg = db.query(ConfigEmailSMTP).first()
    if not cfg:
        raise HTTPException(400, "Configuração SMTP não encontrada.")

    host = (cfg.smtp_host or "").strip()
    port = int(cfg.smtp_port or 0)
    user = (cfg.smtp_user or "").strip()
    pwd  = cfg.smtp_senha or ""
    usar_tls = bool(getattr(cfg, "usar_tls", True))
    from_addr = (cfg.remetente_email or user).strip()

    if not host or not port:
        raise HTTPException(400, "Host/porta inválidos.")
    if not user or not from_addr:
        raise HTTPException(400, "Usuário/Remetente inválidos.")

    logger.info("[SMTP TEST] host=%s port=%s user=%s use_tls=%s", host, port, user, usar_tls)

    ctx = ssl.create_default_context()
    try:
        if usar_tls:
            # STARTTLS típico (Gmail: 587)
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            server.starttls(context=ctx, server_hostname=host)  # <- ESSENCIAL
            server.ehlo()
        else:
            # SSL direto (465)
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=ctx)
            server.ehlo()

        server.login(user, pwd)  # se senha de app estiver errada, explode aqui
        server.noop()            # ping
        server.quit()
        return {"status": "ok"}
    except smtplib.SMTPAuthenticationError as e:
        logger.exception("[SMTP TEST] Auth error")
        raise HTTPException(401, f"Falha de autenticação: {e.smtp_error.decode(errors='ignore') if hasattr(e,'smtp_error') else str(e)}")
    except Exception as e:
        logger.exception("[SMTP TEST] Falha geral")
        raise HTTPException(500, f"Falha na conexão SMTP: {type(e).__name__}: {e}")


# ===== Testar ENVIO DE E-MAIL =====
class TesteEnvioIn(BaseModel):
    para: Optional[List[str]] = None   # se vazio, usa destinatario_interno salvo
    assunto: Optional[str] = "Teste de e-mail - OrderSync"
    corpo_html: Optional[str] = "<p>Este é um e-mail de teste do OrderSync.</p>"

@router.post("/teste_envio")
def testar_envio_email(request: Request,
    body: Optional[TesteEnvioIn] = None):
    db = request.state.db

    # 1) Carrega configs
    msg_cfg = (
        db.query(ConfigEmailMensagem)
        .filter(ConfigEmailMensagem.id == 1)
        .first()
    )
    smtp_cfg = (
        db.query(ConfigEmailSMTP)
        .filter(ConfigEmailSMTP.id == 1)
        .first()
    )

    if not smtp_cfg:
        raise HTTPException(400, "Configuração SMTP não encontrada.")
    if not msg_cfg:
        raise HTTPException(400, "Configuração de mensagem não encontrada.")

    host, port = smtp_cfg.smtp_host, smtp_cfg.smtp_port
    user, pwd = smtp_cfg.smtp_user, (smtp_cfg.smtp_password or "")
    from_addr = (smtp_cfg.email_origem or user or "").strip()
    to_addr = (smtp_cfg.email_teste or user or "").strip()
    if not from_addr or not to_addr:
        raise HTTPException(400, "E-mails de origem/destino inválidos para teste.")

    # 2) Monta mensagem simples (texto puro) – objetivo é só validar conexão/envio
    subject = "Teste SMTP - OrderSync"
    body_txt = "OK. Este é um envio de teste do OrderSync."

    msg = (
        f"Subject: {subject}\n"
        f"From: {from_addr}\n"
        f"To: {to_addr}\n\n"
        f"{body_txt}"
    ).encode("utf-8")

    # 3) Envia (TLS robusto)
    try:
        if smtp_cfg.usar_tls:
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=20)

        if user:
            server.login(user, pwd)

        server.sendmail(from_addr, [to_addr], msg)
        server.quit()
        return {"status": "ok"}
    except Exception as e:
        # Devolve erro legível para você depurar no painel
        raise HTTPException(500, f"Falha no teste SMTP: {type(e).__name__}: {e}")

