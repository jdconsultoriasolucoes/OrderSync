from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import socket
import ssl
from database import SessionLocal
from models.config_email_mensagem import ConfigEmailMensagem
from models.config_email_smtp import ConfigEmailSMTP
from core.deps import get_current_user, get_db
from models.usuario import UsuarioModel
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

# -------------------------


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
    current_user: UsuarioModel = Depends(get_current_user),
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
            atualizado_por=current_user.email,
        )
        db.add(cfg)
    else:
        cfg.destinatario_interno = data.destinatario_interno
        cfg.assunto_padrao = data.assunto_padrao
        cfg.corpo_html = data.corpo_html
        cfg.enviar_para_cliente = data.enviar_para_cliente
        cfg.atualizado_por = current_user.email

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
    current_user: UsuarioModel = Depends(get_current_user),
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
            atualizado_por=current_user.email,
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
        cfg.atualizado_por = current_user.email

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
            # starttls NÃO aceita server_hostname nessa versão
            server.starttls(context=ctx)
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


# payload opcional do teste
class TesteEnvioIn(BaseModel):
    para: Optional[List[str]] = None
    assunto: Optional[str] = "Teste de e-mail - OrderSync"
    corpo_html: Optional[str] = "<p>Este é um e-mail de teste do OrderSync.</p>"

@router.post("/teste_envio")
def testar_envio_email(request: Request, body: Optional[TesteEnvioIn] = None):
    db = request.state.db  # sem Depends(get_db)

    # carrega configs salvas
    msg_cfg = db.query(ConfigEmailMensagem).filter(ConfigEmailMensagem.id == 1).first()
    smtp_cfg = db.query(ConfigEmailSMTP).filter(ConfigEmailSMTP.id == 1).first()
    if not smtp_cfg:
        raise HTTPException(400, "Configuração SMTP não encontrada.")
    if not msg_cfg:
        raise HTTPException(400, "Configuração de mensagem não encontrada.")

    # campos CORRETOS do teu modelo
    host = (smtp_cfg.smtp_host or "").strip()
    port = int(smtp_cfg.smtp_port or 0)
    user = (smtp_cfg.smtp_user or "").strip()
    pwd  = (smtp_cfg.smtp_senha or "").strip()
    usar_tls = bool(getattr(smtp_cfg, "usar_tls", True))
    from_addr = (smtp_cfg.remetente_email or user).strip()

    if not host or not port or not from_addr:
        raise HTTPException(400, "Host/porta/remetente inválidos.")
    if not user or not pwd:
        raise HTTPException(400, "Usuário/senha SMTP ausentes.")

    # destinatários: usa body.para se vier; senão, msg_cfg.destinatario_interno; senão, fallback = remetente
    to_list: List[str] = []
    if body and body.para:
        to_list = [e.strip() for e in body.para if e and e.strip()]
    if not to_list and getattr(msg_cfg, "destinatario_interno", None):
        to_list = [e.strip() for e in msg_cfg.destinatario_interno.split(",") if e.strip()]
    if not to_list:
        to_list = [from_addr]

    assunto = (body.assunto if body and body.assunto else "Teste de e-mail - OrderSync").strip()
    corpo_html = (body.corpo_html if body and body.corpo_html else "<p>Este é um e-mail de teste do OrderSync.</p>")

    # monta mensagem
    msg = MIMEMultipart("alternative")
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    # conexão robusta (Gmail): STARTTLS com server_hostname
    ctx = ssl.create_default_context()
    try:
        if usar_tls:  # 587
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            server.starttls(context=ctx)  # <- sem server_hostname
            server.ehlo()
        else:         # 465
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=ctx)
            server.ehlo()

        server.login(user, pwd)
        server.sendmail(from_addr, to_list, msg.as_string())
        server.quit()
        return {"status": "ok", "to": to_list}
    except smtplib.SMTPAuthenticationError as e:
        # credenciais erradas / senha de app inválida
        raise HTTPException(401, f"Falha de autenticação SMTP: {e}")
    except Exception as e:
        # qualquer outra causa vira 500 com detalhe útil
        raise HTTPException(500, f"Falha no teste SMTP: {type(e).__name__}: {e}")