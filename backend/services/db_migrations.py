import logging
from sqlalchemy import text
from database import SessionLocal

logger = logging.getLogger("ordersync.migrations")

def run_migrations():
    """
    Verifica e aplica migrações de schema (colunas novas)
    que o Alembic não gerencia ou para evitar complexidade de migration tools.
    """
    logger.info("Iniciando migrações de schema...")
    with SessionLocal() as db:
        # 1. ConfigEmailMensagem: assunto_cliente, corpo_html_cliente
        try:
            db.execute(text("SELECT assunto_cliente FROM config_email_mensagem LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando colunas de email cliente na config_email_mensagem...")
            try:
                db.execute(text("ALTER TABLE config_email_mensagem ADD COLUMN assunto_cliente TEXT"))
                db.execute(text("ALTER TABLE config_email_mensagem ADD COLUMN corpo_html_cliente TEXT"))
                db.commit()
                logger.info("Colunas adicionadas com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar colunas: {e}")

    logger.info("Migrações concluídas.")
