from sqlalchemy import Column, Integer, Text, Boolean
from database import Base  # usa o Base que você já tem em database.py

class ConfigEmailMensagem(Base):
    __tablename__ = "config_email_mensagem"

    id = Column(Integer, primary_key=True, index=True)
    destinatario_interno = Column(Text, nullable=False)   # ex: "pedidos@empresa.com, comercial@empresa.com"
    assunto_padrao = Column(Text, nullable=False)         # ex: "Novo pedido {{pedido_id}} - {{cliente_nome}}"
    corpo_html = Column(Text, nullable=False)             # corpo com placeholders
    enviar_para_cliente = Column(Boolean, nullable=False, default=False)
