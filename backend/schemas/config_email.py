from pydantic import BaseModel
from typing import Optional

# ---------- MENSAGEM / DESTINO (aba 'Mensagens e Destinatários') ----------

class ConfigEmailMensagemBase(BaseModel):
    destinatario_interno: str            # pode ter vários e-mails separados por vírgula
    assunto_padrao: str
    corpo_html: str
    enviar_para_cliente: bool

class ConfigEmailMensagemOut(ConfigEmailMensagemBase):
    id: int
    class Config:
        orm_mode = True


# ---------- SMTP / REMETENTE (aba 'Remetente e SMTP') ----------

class ConfigEmailSMTPBase(BaseModel):
    remetente_email: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    usar_tls: bool

class ConfigEmailSMTPUpdate(ConfigEmailSMTPBase):
    smtp_senha: Optional[str] = None     # só manda se quiser trocar

class ConfigEmailSMTPOut(ConfigEmailSMTPBase):
    id: int
    class Config:
        orm_mode = True
