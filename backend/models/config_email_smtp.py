from sqlalchemy import Column, Integer, Text, Boolean
from database import Base

class ConfigEmailSMTP(Base):
    __tablename__ = "config_email_smtp"

    id = Column(Integer, primary_key=True, index=True)

    remetente_email = Column(Text, nullable=False)  # "pedidos@empresa.com"
    smtp_host       = Column(Text, nullable=False)  # "smtp.seudominio.com"
    smtp_port       = Column(Integer, nullable=False)  # 587, 465...
    smtp_user       = Column(Text, nullable=False)
    smtp_senha      = Column(Text, nullable=False)  # depois podemos criptografar / esconder
    usar_tls        = Column(Boolean, nullable=False, default=True)