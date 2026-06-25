import sys
import os
import logging
from sqlalchemy import text
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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

        # 6. tb_pedidos_itens: preco_unit_frt, subtotal_com_f, subtotal_sem_f, peso_kg, valor_frete_unitario, markup, valor_final_markup, valor_s_frete_markup
        for col, col_type in [("preco_unit_frt", "NUMERIC"), ("subtotal_com_f", "NUMERIC"), ("subtotal_sem_f", "NUMERIC"), ("peso_kg", "NUMERIC"), ("valor_frete_unitario", "NUMERIC"), ("markup", "NUMERIC"), ("valor_final_markup", "NUMERIC"), ("valor_s_frete_markup", "NUMERIC")]:
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

        # 16. tb_pedidos_itens: manual_freight
        try:
            db.execute(text("SELECT manual_freight FROM tb_pedidos_itens LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando coluna manual_freight em tb_pedidos_itens...")
            try:
                db.execute(text("ALTER TABLE tb_pedidos_itens ADD COLUMN manual_freight BOOLEAN DEFAULT FALSE"))
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar manual_freight em tb_pedidos_itens: {e}")

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


        # 12. Correção Global de Autoincremento (Catálogo)
        tables_to_fix = [
            ('tb_referencias', 'codigo'),
            ('tb_cidade_supervisor', 'codigo'),
            ('tb_canal_venda', 'Id'),
            ('tb_municipio_rota', 'id'),
            ('tb_supervisores', 'id')
        ]
        
        for table, pk in tables_to_fix:
            try:
                # Verifica se já tem default (autoincrement)
                res = db.execute(text(f"""
                    SELECT column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{pk}'
                """)).scalar()
                
                if not res or 'nextval' not in str(res):
                    logger.info(f"Configurando autoincremento para {table}.{pk}...")
                    seq_name = f"{table}_{pk.lower()}_seq"
                    db.execute(text(f'CREATE SEQUENCE IF NOT EXISTS "{seq_name}"'))
                    db.execute(text(f'ALTER TABLE "{table}" ALTER COLUMN "{pk}" SET DEFAULT nextval(\'{seq_name}\')'))
                    db.execute(text(f'ALTER SEQUENCE "{seq_name}" OWNED BY "{table}"."{pk}"'))
                    db.execute(text(f'SELECT setval(\'{seq_name}\', COALESCE((SELECT MAX("{pk}") FROM "{table}"), 0) + 1, false)'))
                    db.commit()
                    logger.info(f"Autoincremento configurado para {table}.")
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao configurar autoincremento em {table}: {e}")

        # 13. CidadeSupervisor: gerente_insumos, gerente_pet
        for col in ["gerente_insumos", "gerente_pet"]:
            try:
                db.execute(text(f"SELECT {col} FROM tb_cidade_supervisor LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em tb_cidade_supervisor...")
                try:
                    db.execute(text(f"ALTER TABLE tb_cidade_supervisor ADD COLUMN {col} VARCHAR"))
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar {col} em tb_cidade_supervisor: {e}")

        # 14. Limpeza de Duplicados em tb_pedidos (Resolução de erro de salvamento)
        try:
            logger.info("Verificando duplicados em tb_pedidos...")
            # Query para identificar se existem duplicados
            dup_count = db.execute(text("SELECT COUNT(*) FROM (SELECT id_pedido FROM public.tb_pedidos GROUP BY id_pedido HAVING COUNT(*) > 1) sub")).scalar()
            if dup_count and dup_count > 0:
                logger.warning(f"Detectados {dup_count} IDs duplicados em tb_pedidos. Iniciando limpeza...")
                # Mantém apenas a versão mais recente de cada ID
                db.execute(text("""
                    DELETE FROM public.tb_pedidos
                    WHERE ctid NOT IN (
                        SELECT MAX(ctid)
                        FROM public.tb_pedidos
                        GROUP BY id_pedido
                    )
                """))
                db.commit()
                logger.info("Limpeza de duplicados concluída com sucesso.")
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao limpar duplicados em tb_pedidos: {e}")

        # 15. Garantir Constraint Unique em id_pedido
        try:
            db.execute(text("ALTER TABLE public.tb_pedidos ADD CONSTRAINT unique_id_pedido UNIQUE (id_pedido)"))
            db.commit()
            logger.info("Constraint UNIQUE adicionada em tb_pedidos.id_pedido.")
        except Exception:
            db.rollback()
            # Se já existir, ignoramos
            pass

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

        # 17. tb_pedidos: valor_ajuste, data_faturamento
        for col, col_type in [("valor_ajuste", "NUMERIC DEFAULT 0.0"), ("data_faturamento", "TIMESTAMP WITHOUT TIME ZONE")]:
            try:
                db.execute(text(f"SELECT {col} FROM tb_pedidos LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em tb_pedidos...")
                try:
                    db.execute(text(f"ALTER TABLE tb_pedidos ADD COLUMN {col} {col_type}"))
                    db.commit()
                    logger.info(f"Coluna {col} adicionada com sucesso em tb_pedidos.")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar {col} em tb_pedidos: {e}")

        # 18. Tabela tb_pedidos_importados (Log de importação Excel)
        try:
            db.execute(text("SELECT 1 FROM tb_pedidos_importados LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Criando tabela tb_pedidos_importados...")
            try:
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS public.tb_pedidos_importados (
                        id BIGSERIAL PRIMARY KEY,
                        pedido_supra VARCHAR,
                        emissao TIMESTAMP WITHOUT TIME ZONE,
                        cliente_retira VARCHAR,
                        peso NUMERIC,
                        valor_pedido NUMERIC,
                        danfe VARCHAR,
                        codigo_cliente VARCHAR,
                        data_pedido TIMESTAMP WITHOUT TIME ZONE,
                        status_pedido_excel VARCHAR,
                        status_processamento VARCHAR,
                        ajuste_gerado NUMERIC DEFAULT 0,
                        detalhes_processamento TEXT,
                        importado_em TIMESTAMP DEFAULT NOW()
                    )
                """))
                db.commit()
                logger.info("Tabela tb_pedidos_importados criada com sucesso.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao criar tb_pedidos_importados: {e}")

        # 19. Status de Pedido: PEDIDO_NAO_COMPLETO
        try:
            res = db.execute(text("SELECT 1 FROM pedido_status WHERE codigo = 'PEDIDO_NAO_COMPLETO'")).scalar()
            if not res:
                logger.info("Inserindo status PEDIDO_NAO_COMPLETO em pedido_status...")
                db.execute(text("""
                    INSERT INTO public.pedido_status (codigo, rotulo, cor_hex, ordem, ativo)
                    VALUES ('PEDIDO_NAO_COMPLETO', 'Pedido Não Completo', '#EF4444', 6, TRUE)
                """))
                db.commit()
                logger.info("Status PEDIDO_NAO_COMPLETO inserido com sucesso.")
        except Exception as e:
            db.rollback()
            logger.error(f"Falha ao inserir status PEDIDO_NAO_COMPLETO: {e}")

        # 20. CadastroCliente: elaboracao_placa_veiculo, elaboracao_proprietario_veiculo
        for col in ["elaboracao_placa_veiculo", "elaboracao_proprietario_veiculo"]:
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

        # 21. Pré-popular tabelas de Ramo de Atividade, Atividade Principal e Filiais
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS tb_ramo_atividade (
                    id SERIAL PRIMARY KEY,
                    ramo_atividade VARCHAR
                )
            """))
            db.commit()
            
            cnt = db.execute(text("SELECT COUNT(*) FROM tb_ramo_atividade")).scalar()
            if cnt == 0:
                logger.info("Pré-populando tb_ramo_atividade...")
                from data.listas import RAMO_DE_ATIVIDADE
                for ramo in RAMO_DE_ATIVIDADE:
                    db.execute(text("INSERT INTO tb_ramo_atividade (ramo_atividade) VALUES (:val)"), {"val": ramo})
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao popular tb_ramo_atividade: {e}")

        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS tb_atividade_principal (
                    id SERIAL PRIMARY KEY,
                    atividade_principal VARCHAR
                )
            """))
            db.commit()
            
            cnt = db.execute(text("SELECT COUNT(*) FROM tb_atividade_principal")).scalar()
            if cnt == 0:
                logger.info("Pré-populando tb_atividade_principal...")
                from data.listas import ATIVIDADE_PRINCIPAL
                for atividade in ATIVIDADE_PRINCIPAL:
                    db.execute(text("INSERT INTO tb_atividade_principal (atividade_principal) VALUES (:val)"), {"val": atividade})
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao popular tb_atividade_principal: {e}")

        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS tb_filiais (
                    id SERIAL PRIMARY KEY,
                    filial VARCHAR
                )
            """))
            db.commit()
            
            cnt = db.execute(text("SELECT COUNT(*) FROM tb_filiais")).scalar()
            if cnt == 0:
                logger.info("Pré-populando tb_filiais...")
                filiais_set = {"Matriz SUPRA LOG"}
                try:
                    rows = db.execute(text("SELECT DISTINCT fornecedor FROM t_cadastro_produto_v2 WHERE fornecedor IS NOT NULL AND fornecedor != ''")).scalars().all()
                    for r in rows:
                        filiais_set.add(r.strip())
                except Exception:
                    pass
                for f in sorted(list(filiais_set)):
                    db.execute(text("INSERT INTO tb_filiais (filial) VALUES (:val)"), {"val": f})
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao popular tb_filiais: {e}")

        # 22. CadastroCliente: comissao_pet_dispet_flag, comissao_insumos_dispet_flag
        for col in ["comissao_pet_dispet_flag", "comissao_insumos_dispet_flag"]:
            try:
                db.execute(text(f"SELECT {col} FROM t_cadastro_cliente_v2 LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info(f"Adicionando coluna {col} em t_cadastro_cliente_v2...")
                try:
                    db.execute(text(f"ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN {col} BOOLEAN DEFAULT TRUE"))
                    db.execute(text(f"UPDATE t_cadastro_cliente_v2 SET {col} = TRUE"))
                    db.commit()
                    logger.info(f"Coluna {col} adicionada com sucesso.")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Falha ao adicionar coluna {col}: {e}")

        # 23. Status de Pedido: Carga em formação
        try:
            res = db.execute(text("SELECT 1 FROM pedido_status WHERE codigo = 'Carga em formação'")).scalar()
            if not res:
                logger.info("Inserindo status Carga em formação em pedido_status...")
                db.execute(text("""
                    INSERT INTO public.pedido_status (codigo, rotulo, cor_hex, ordem, ativo)
                    VALUES ('Carga em formação', 'Carga em formação', '#fef3c7', 7, TRUE)
                """))
                db.commit()
                logger.info("Status Carga em formação inserido com sucesso.")
        except Exception as e:
            db.rollback()
            logger.error(f"Falha ao inserir status Carga em formação: {e}")

        # 24. tb_pedidos: valor_nota
        try:
            db.execute(text("SELECT valor_nota FROM tb_pedidos LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando coluna valor_nota em tb_pedidos...")
            try:
                db.execute(text("ALTER TABLE tb_pedidos ADD COLUMN valor_nota NUMERIC"))
                db.commit()
                logger.info("Coluna valor_nota adicionada com sucesso em tb_pedidos.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar valor_nota em tb_pedidos: {e}")

        # 25. t_cadastro_produto_v2: nome_arquivo_estoque
        try:
            db.execute(text("SELECT nome_arquivo_estoque FROM t_cadastro_produto_v2 LIMIT 1"))
        except Exception:
            db.rollback()
            logger.info("Adicionando coluna nome_arquivo_estoque em t_cadastro_produto_v2...")
            try:
                db.execute(text("ALTER TABLE t_cadastro_produto_v2 ADD COLUMN nome_arquivo_estoque TEXT"))
                db.commit()
                logger.info("Coluna nome_arquivo_estoque adicionada com sucesso em t_cadastro_produto_v2.")
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao adicionar nome_arquivo_estoque em t_cadastro_produto_v2: {e}")

    logger.info("Todas as migrações concluídas.")


if __name__ == "__main__":
    run_migrations()
