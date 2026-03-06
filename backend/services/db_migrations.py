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

                logger.error(f"Falha ao adicionar colunas: {e}")

        # 2. Usuario: email_verificado, token_verificacao
        try:
            db.execute(text("SELECT email_verificado FROM t_usuario LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando colunas de verificação de email em t_usuario...")
            try:
                db.execute(text("ALTER TABLE t_usuario ADD COLUMN email_verificado BOOLEAN DEFAULT FALSE"))
                db.execute(text("ALTER TABLE t_usuario ADD COLUMN token_verificacao TEXT"))
                # Mark existing users as verified to avoid lockout
                db.execute(text("UPDATE t_usuario SET email_verificado = TRUE"))
                db.commit()
                logger.info("Colunas de verificação adicionadas com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar colunas em t_usuario: {e}")

        # 3. CadastroCliente: cadastro_periodo_de_compra
        try:
            db.execute(text("SELECT cadastro_periodo_de_compra FROM t_cadastro_cliente_v2 LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando coluna cadastro_periodo_de_compra em t_cadastro_cliente_v2...")
            try:
                db.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN cadastro_periodo_de_compra VARCHAR"))
                db.commit()
                logger.info("Coluna cadastro_periodo_de_compra adicionada com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar coluna em t_cadastro_cliente_v2: {e}")

        # 4. tb_cargas: nome_carga
        try:
            db.execute(text("SELECT nome_carga FROM tb_cargas LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando coluna nome_carga em tb_cargas...")
            try:
                db.execute(text("ALTER TABLE tb_cargas ADD COLUMN nome_carga VARCHAR"))
                db.commit()
                logger.info("Coluna nome_carga adicionada com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar coluna em tb_cargas: {e}")

    logger.info("Migrações concluídas.")
