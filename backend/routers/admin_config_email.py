from fastapi import APIRouter, Depends, HTTPException
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

@router.post("/smtp/teste")
def testar_smtp_conexao(
    data: Optional[TesteSMTPIn] = None,
    db: Session = Depends(get_db),
):
    saved = db.query(ConfigEmailSMTP).filter(ConfigEmailSMTP.id == 1).first()

    if not data and not saved:
        raise HTTPException(400, "Configuração SMTP não encontrada.")

    # ---- Monta credenciais efetivas (body tem prioridade) ----
    host = (data.smtp_host or "").strip() if data and data.smtp_host else (saved.smtp_host or "").strip()
    port_raw = (data.smtp_port if data and data.smtp_port is not None else saved.smtp_port if saved else 587)
    try:
        port = int(port_raw) if port_raw is not None else 587
    except Exception:
        port = 587

    user = (data.smtp_user or "").strip() if data and data.smtp_user else (saved.smtp_user or "").strip()

    body_pwd = ((data.smtp_senha or "").strip() if data else "")
    pwd = body_pwd if body_pwd else (saved.smtp_senha or "")
    pwd = "".join((pwd or "").split())  # remove todos os espaços/brancos
    user = (user or "").strip()
    host = (host or "").strip()

    # Inferir TLS se não vier marcado
    if data and data.usar_tls is not None:
        use_tls = bool(data.usar_tls)
    else:
        # padrão seguro: porta 465 -> SSL; 587 -> STARTTLS
        use_tls = (port != 465)

    # ---- Validações simples ----
    if not host:
        raise HTTPException(400, "Host SMTP não informado.")
    if not port:
        raise HTTPException(400, "Porta SMTP não informada.")
    if not user or not pwd:
        raise HTTPException(400, "Usuário e senha são obrigatórios para o teste.")

    # ---- Conexão ----
    try:
        if port == 465:
            # SSL directo (Gmail: smtp.gmail.com:465)
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
        else:
            # Porta 587: plain + STARTTLS
            server = smtplib.SMTP(host, port, timeout=20)
            if use_tls:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()

        server.login(user, pwd)
        server.quit()
        return {"ok": True, "host": host, "port": port, "tls": (port != 465), "message": "Conexão SMTP OK"}

    except smtplib.SMTPAuthenticationError as e:
        # credenciais inválidas
        code = getattr(e, 'smtp_code', 401) or 401
        detail = "Falha de autenticação SMTP (verifique usuário/senha de app)."
        raise HTTPException(status_code=401, detail={"code": code, "error": detail})

    except smtplib.SMTPConnectError as e:
        # servidor recusou conexão
        code = getattr(e, 'smtp_code', 502) or 502
        msg = getattr(e, 'smtp_error', b'').decode(errors='ignore') if hasattr(e, 'smtp_error') else str(e)
        raise HTTPException(status_code=502, detail={"code": code, "error": f"Não conectou ao servidor SMTP: {msg}"})

    except smtplib.SMTPServerDisconnected as e:
        raise HTTPException(status_code=502, detail={"error": f"Servidor desconectou: {e}"})

    except smtplib.SMTPHeloError as e:
        raise HTTPException(status_code=502, detail={"error": f"Erro no HELO/EHLO: {e}"})

    except smtplib.SMTPException as e:
        # outros erros de protocolo
        raise HTTPException(status_code=502, detail={"error": f"Erro SMTP: {e}"})

    except (socket.gaierror, socket.timeout) as e:
        # DNS / timeout
        raise HTTPException(status_code=504, detail={"error": f"Rede/DNS/timeout ao conectar em {host}:{port} - {e}"})

    except ssl.SSLError as e:
        # mismatch TLS (ex.: usar SSL na 587 ou STARTTLS na 465)
        raise HTTPException(status_code=495, detail={"error": f"Erro TLS/SSL: {e}. Dica: 587 + STARTTLS (use_tls=True) ou 465 + SSL."})

    except Exception as e:
        # catch-all sem vazar senha
        raise HTTPException(status_code=500, detail={"error": f"Erro inesperado ao testar SMTP: {e}"})

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
    

