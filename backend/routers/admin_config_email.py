from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


router = APIRouter(
    prefix="/admin/config_email",
    tags=["Admin - Config Email"],
    # IMPORTANTE: aqui precisa de proteção de acesso (auth funcionário)
    # Ex.: dependencies=[Depends(verify_admin_user)]
)

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
@router.post("/smtp/teste")
def testar_smtp_conexao(
    data: Optional[ConfigEmailSMTPUpdate] = None,
    db: Session = Depends(get_db),
):
    """
    Tenta conectar e fazer login no servidor SMTP.
    Usa o payload (se enviado) ou a configuração salva (id=1).
    """
    if data is None:
        cfg = (
            db.query(ConfigEmailSMTP)
            .filter(ConfigEmailSMTP.id == 1)
            .first()
        )
        if not cfg:
            raise HTTPException(400, "Configuração SMTP não encontrada.")
        host, port = cfg.smtp_host, cfg.smtp_port
        user, pwd = cfg.smtp_user, cfg.smtp_senha
        use_tls   = cfg.usar_tls
    else:
        host, port = data.smtp_host, data.smtp_port
        user, pwd  = data.smtp_user, (data.smtp_senha or "")
        use_tls    = data.usar_tls

    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=20)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=20)

        server.login(user, pwd)
        server.quit()
        return {"ok": True, "message": "Conexão SMTP OK"}
    except smtplib.SMTPAuthenticationError as e:
        # 401 deixa claro para o front
        raise HTTPException(status_code=401, detail=f"Falha de autenticação SMTP: {getattr(e, 'smtp_error', e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro SMTP: {e}")


# ===== Testar ENVIO DE E-MAIL =====
class TesteEnvioIn(BaseModel):
    para: Optional[List[str]] = None   # se vazio, usa destinatario_interno salvo
    assunto: Optional[str] = "Teste de e-mail - OrderSync"
    corpo_html: Optional[str] = "<p>Este é um e-mail de teste do OrderSync.</p>"

@router.post("/teste_envio")
def testar_envio_email(
    body: Optional[TesteEnvioIn] = None,
    db: Session = Depends(get_db),
):
    # carrega configs salvas
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

    # destinatários
    to_list: List[str] = []
    if body and body.para:
        to_list = body.para
    else:
        to_list = [x.strip() for x in (msg_cfg.destinatario_interno or "").split(",") if x.strip()]

    if not to_list:
        raise HTTPException(400, "Informe pelo menos um destinatário (ou configure destinatário interno).")

    # monta mensagem simples
    subject = (body.assunto if body and body.assunto else "Teste de e-mail - OrderSync")
    html    = (body.corpo_html if body and body.corpo_html else "<p>Este é um e-mail de teste do OrderSync.</p>")

    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_cfg.remetente_email or smtp_cfg.smtp_user
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    # envia
    try:
        if smtp_cfg.usar_tls:
            server = smtplib.SMTP(smtp_cfg.smtp_host, smtp_cfg.smtp_port, timeout=20)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_cfg.smtp_host, smtp_cfg.smtp_port, timeout=20)

        server.login(smtp_cfg.smtp_user, smtp_cfg.smtp_senha)
        server.sendmail(msg["From"], to_list, msg.as_string())
        server.quit()
        return {"ok": True, "message": "E-mail de teste enviado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no envio: {e}")