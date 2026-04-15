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
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar coluna em tb_cargas: {e}")

        # 5. tb_pedidos: data_retirada, tabela_preco_nome, fornecedor
        for col, col_type in [("data_retirada", "DATE"), ("tabela_preco_nome", "VARCHAR"), ("fornecedor", "VARCHAR")]:
            try:
                db.execute(text(f"SELECT {col} FROM tb_pedidos LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em tb_pedidos...")
                try:
                    db.execute(text(f"ALTER TABLE tb_pedidos ADD COLUMN {col} {col_type}"))
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar {col} em tb_pedidos: {e}")

        # 6. tb_pedidos_itens: preco_unit_frt, subtotal_com_f, subtotal_sem_f, peso_kg
        for col, col_type in [("preco_unit_frt", "NUMERIC"), ("subtotal_com_f", "NUMERIC"), ("subtotal_sem_f", "NUMERIC"), ("peso_kg", "NUMERIC")]:
            try:
                db.execute(text(f"SELECT {col} FROM tb_pedidos_itens LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em tb_pedidos_itens...")
                try:
                    db.execute(text(f"ALTER TABLE tb_pedidos_itens ADD COLUMN {col} {col_type}"))
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar {col} em tb_pedidos_itens: {e}")

        # 7. tb_transporte: capacidade_kg, modelo, tipo_veiculo
        for col, col_type in [("capacidade_kg", "INTEGER"), ("modelo", "VARCHAR"), ("tipo_veiculo", "VARCHAR")]:
            try:
                db.execute(text(f"SELECT {col} FROM tb_transporte LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em tb_transporte...")
                try:
                    db.execute(text(f"ALTER TABLE tb_transporte ADD COLUMN {col} {col_type}"))
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar {col} em tb_transporte: {e}")

        # 8. CadastroCliente: elaboracao_vendedor
        try:
            db.execute(text("SELECT elaboracao_vendedor FROM t_cadastro_cliente_v2 LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando coluna elaboracao_vendedor em t_cadastro_cliente_v2...")
            try:
                db.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN elaboracao_vendedor VARCHAR"))
                db.commit()
                logger.info("Coluna elaboracao_vendedor adicionada com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar coluna elaboracao_vendedor em t_cadastro_cliente_v2: {e}")

        # 9. tb_cargas: is_historico, data_faturamento, faturado_por_id
        try:
            db.execute(text("SELECT is_historico FROM tb_cargas LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando colunas de histórico em tb_cargas...")
            try:
                db.execute(text("ALTER TABLE tb_cargas ADD COLUMN is_historico BOOLEAN DEFAULT FALSE"))
                db.execute(text("ALTER TABLE tb_cargas ADD COLUMN data_faturamento TIMESTAMP WITHOUT TIME ZONE"))
                db.execute(text("ALTER TABLE tb_cargas ADD COLUMN faturado_por_id BIGINT"))
                db.commit()
                logger.info("Colunas de histórico adicionadas com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar colunas de histórico em tb_cargas: {e}")

    logger.info("Migrações concluídas.")

    # 10. CadastroCliente: elaboracao_gerente_insumos, elaboracao_gerente_pet
    with SessionLocal() as db:
        for col in ["elaboracao_gerente_insumos", "elaboracao_gerente_pet"]:
            try:
                db.execute(text(f"SELECT {col} FROM t_cadastro_cliente_v2 LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em t_cadastro_cliente_v2...")
                try:
                    db.execute(text(f"ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN {col} VARCHAR"))
                    db.commit()
                    logger.info(f"Coluna {col} adicionada com sucesso.")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar coluna {col}: {e}")

        # 11. Tabela t_profile_config (configuracao global do representante)
        try:
            db.execute(text("SELECT 1 FROM t_profile_config LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Criando tabela t_profile_config...")
            try:
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS t_profile_config (
                        id BIGSERIAL PRIMARY KEY,
                        codigo_representante VARCHAR,
                        cnpj VARCHAR,
                        razao_social VARCHAR,
                        endereco VARCHAR,
                        data_criacao TIMESTAMP DEFAULT NOW(),
                        data_atualizacao TIMESTAMP DEFAULT NOW()
                    )
                """))
                # Insere registro default (singleton)
                db.execute(text("""
                    INSERT INTO t_profile_config (codigo_representante, cnpj, razao_social, endereco)
                    SELECT '', '', '', ''
                    WHERE NOT EXISTS (SELECT 1 FROM t_profile_config)
                """))
                db.commit()
                logger.info("Tabela t_profile_config criada com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao criar t_profile_config: {e}")

    logger.info("Todas as migrações concluídas.")
