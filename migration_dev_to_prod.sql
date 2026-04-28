-- ============================================================
-- MIGRATION SCRIPT: DEV -> PROD
-- Generated 2026-02-28 | All statements are idempotent.
-- Apply on PROD database via Render Shell or psql.
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Sequences
CREATE SEQUENCE IF NOT EXISTS cliente_v2_id_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS config_email_mensagem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 2147483647
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS config_email_smtp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 2147483647
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_familia_insumos
    AS bigint
    START WITH 300
    INCREMENT BY 10
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_tabela_preco_id_tabela
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS t_cadastro_produto_v2_id_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS t_imposto_v2_id_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS t_preco_produto_pdf_v2_id_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS tb_background_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 2147483647
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS tb_pedidos_id_pedido_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS tb_pedidos_itens_id_item_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS usuario_id_seq
    AS bigint
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    NO CYCLE;


-- Tables (ordered by FK dependency)

CREATE TABLE IF NOT EXISTS config_email_mensagem (
    id INTEGER DEFAULT nextval('config_email_mensagem_id_seq'::regclass) NOT NULL,
    destinatario_interno TEXT NOT NULL,
    assunto_padrao TEXT NOT NULL,
    corpo_html TEXT NOT NULL,
    enviar_para_cliente BOOLEAN DEFAULT false NOT NULL,
    atualizado_por VARCHAR,
    assunto_cliente TEXT,
    corpo_html_cliente TEXT,
    CONSTRAINT config_email_mensagem_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS config_email_smtp (
    id INTEGER DEFAULT nextval('config_email_smtp_id_seq'::regclass) NOT NULL,
    remetente_email TEXT NOT NULL,
    smtp_host TEXT NOT NULL,
    smtp_port INTEGER NOT NULL,
    smtp_user TEXT NOT NULL,
    smtp_senha TEXT NOT NULL,
    usar_tls BOOLEAN DEFAULT true NOT NULL,
    atualizado_por VARCHAR,
    CONSTRAINT config_email_smtp_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS criacao_tabela_preco (
    "codigo tratado" INTEGER,
    "Cliente" VARCHAR(250),
    "Produto" VARCHAR(250),
    "Cond. Pagto" VARCHAR(250),
    "Descri��o" VARCHAR(250)
);

CREATE TABLE IF NOT EXISTS lista_precos (
    id INTEGER NOT NULL,
    fornecedor VARCHAR(120),
    lista VARCHAR(50),
    familia VARCHAR(200),
    codigo VARCHAR(80) NOT NULL,
    descricao VARCHAR(500) NOT NULL,
    preco_ton NUMERIC(14,2),
    preco_sc NUMERIC(14,2),
    page INTEGER,
    ingest_timestamp TIMESTAMPTZ,
    CONSTRAINT lista_precos_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS lista_produto (
    codigo_supra VARCHAR(250),
    status_produto VARCHAR(250),
    nome_produto VARCHAR(250),
    tipo_giro VARCHAR(250),
    estoque_disponivel INTEGER,
    unidade VARCHAR(250),
    unidade_anterior VARCHAR(250),
    peso REAL,
    peso_bruto REAL,
    estoque_ideal INTEGER,
    embalagem_venda VARCHAR(250),
    unidade_embalagem VARCHAR(250),
    codigo_ean VARCHAR(250),
    codigo_embalagem VARCHAR(250),
    ncm VARCHAR(250),
    fornecedor VARCHAR(250),
    filhos INTEGER,
    familia VARCHAR(250),
    preco VARCHAR(250),
    preco_anterior VARCHAR(250),
    preco_tonelada VARCHAR(250),
    validade_tabela VARCHAR(250),
    validade_tabela_anterior VARCHAR(250),
    desconto_valor_tonelada VARCHAR(250),
    data_desconto_inicio VARCHAR(250),
    data_desconto_fim VARCHAR(250),
    preco_final INTEGER,
    tipo VARCHAR(250),
    tipo_alteracao VARCHAR(250),
    preco_tonelada_anterior INTEGER,
    marca VARCHAR(250),
    id_familia INTEGER
);

CREATE TABLE IF NOT EXISTS pedido_status (
    id UUID DEFAULT gen_random_uuid(),
    codigo TEXT,
    rotulo TEXT,
    cor_hex TEXT,
    ordem INTEGER,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "public.depara_produtos" (
    "código do produto" VARCHAR(50),
    nome VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS t_cadastro_cliente (
    codigo BIGINT,
    nome_empresarial TEXT,
    nome_fantasia TEXT,
    tipo_pessoa TEXT,
    ramo_juridico TEXT,
    atividade_principal TEXT,
    contato_comprador TEXT,
    telefone_contato TEXT,
    email_contato TEXT,
    ativo_nao_ativo TEXT,
    ocorrencia TEXT,
    retira_sim_nao_faturamento TEXT,
    endereco_faturamento TEXT,
    numero_faturamento TEXT,
    bairro_faturamento TEXT,
    cep_faturamento TEXT,
    cidade_faturamento TEXT,
    uf_faturamento TEXT,
    cnpj_cpf_faturamento TEXT,
    inscricao_estadual_faturamento TEXT,
    telefone_faturamento TEXT,
    "e-mail_faturamento" TEXT,
    cidade_entrega TEXT,
    km_entrega BIGINT,
    rota_entrega BIGINT,
    id_entrega BIGINT,
    sugestao_de_frete_to_entrega DOUBLE PRECISION,
    endereco_entrega TEXT,
    observacao_entrega TEXT,
    contato_entrega TEXT,
    telefone_entrega TEXT,
    "e-mail_entrega" TEXT,
    mensagem_faturamento_entrega TEXT,
    mensagem_motorista_entrega TEXT,
    contato_cobranca TEXT,
    telefone_cobranca TEXT,
    email_cobranca TEXT,
    cidade_cobranca TEXT,
    endereco_cobranca TEXT,
    supervisor_alisul TEXT,
    tipo_de_cliente_alisul TEXT,
    data_ocorrencia_alisul TIMESTAMP,
    observacoes_alisul_1 TEXT,
    observacoes_alisul_2 TEXT,
    bairro_faturamento_formatted TEXT,
    cidade_faturamento_formatted TEXT,
    cnpj_cpf_faturamento_formatted TEXT,
    cidade_entrega_formatted TEXT,
    cidade_cobranca_formatted TEXT
);

CREATE TABLE IF NOT EXISTS t_cadastro_cliente_v2 (
    id BIGINT NOT NULL,
    cadastro_codigo_da_empresa VARCHAR,
    cadastro_ativo BOOLEAN,
    cadastro_tipo_cliente VARCHAR,
    cadastro_tipo_venda VARCHAR,
    cadastro_tipo_compra VARCHAR,
    cadastro_limite_credito DOUBLE PRECISION,
    cadastro_nome_cliente VARCHAR,
    cadastro_nome_fantasia VARCHAR,
    cadastro_cnpj VARCHAR,
    cadastro_inscricao_estadual VARCHAR,
    cadastro_cpf VARCHAR,
    cadastro_situacao VARCHAR,
    cadastro_indicacao_cliente VARCHAR,
    cadastro_ramo_de_atividade VARCHAR,
    cadastro_atividade_principal VARCHAR,
    cadastro_markup DOUBLE PRECISION,
    compras_nome_responsavel VARCHAR,
    compras_celular_responsavel VARCHAR,
    compras_email_resposavel VARCHAR,
    compras_data_nascimento_resposavel VARCHAR,
    compras_observacoes_responsavel VARCHAR,
    compras_filial_resposavel VARCHAR,
    faturamento_endereco VARCHAR,
    faturamento_bairro VARCHAR,
    faturamento_cep VARCHAR,
    faturamento_localizacao VARCHAR,
    faturamento_municipio VARCHAR,
    faturamento_estado VARCHAR,
    faturamento_email_danfe VARCHAR,
    legal_nome VARCHAR,
    legal_celular VARCHAR,
    legal_email VARCHAR,
    legal_data_nascimento VARCHAR,
    legal_observacoes VARCHAR,
    entrega_endereco VARCHAR,
    entrega_bairro VARCHAR,
    entrega_cep VARCHAR,
    entrega_localizacao VARCHAR,
    entrega_municipio VARCHAR,
    entrega_estado VARCHAR,
    entrega_rota_principal VARCHAR,
    entrega_rota_aproximacao VARCHAR,
    entrega_observacao_motorista VARCHAR,
    recebimento_nome VARCHAR,
    recebimento_celular VARCHAR,
    recebimento_email VARCHAR,
    recebimento_data_nascimento VARCHAR,
    recebimento_observacoes VARCHAR,
    cobranca_endereco VARCHAR,
    cobranca_bairro VARCHAR,
    cobranca_cep VARCHAR,
    cobranca_localizacao VARCHAR,
    cobranca_municipio VARCHAR,
    cobranca_estado VARCHAR,
    cobranca_resp_nome VARCHAR,
    cobranca_resp_celular VARCHAR,
    cobranca_resp_email VARCHAR,
    cobranca_resp_data_nascimento VARCHAR,
    cobranca_resp_observacoes VARCHAR,
    ultimas_compras_numero_danfe VARCHAR,
    ultimas_compras_emissao VARCHAR,
    ultimas_compras_valor_total DOUBLE PRECISION,
    ultimas_compras_valor_frete DOUBLE PRECISION,
    ultimas_compras_valor_frete_padrao DOUBLE PRECISION,
    ultimas_compras_valor_ultimo_frete DOUBLE PRECISION,
    ultimas_compras_lista_tabela VARCHAR,
    ultimas_compras_condicoes_pagamento VARCHAR,
    ultimas_compras_cliente_calcula_st VARCHAR,
    ultimas_compras_prazo_medio VARCHAR,
    ultimas_compras_previsao_proxima VARCHAR,
    obs_nao_compra_observacoes VARCHAR,
    elaboracao_classificacao VARCHAR,
    elaboracao_tipo_venda VARCHAR,
    elaboracao_limite_credito DOUBLE PRECISION,
    elaboracao_data_vencimento VARCHAR,
    grupo_economico_codigo VARCHAR,
    grupo_economico_nome VARCHAR,
    ref_comercial_empresa VARCHAR,
    ref_comercial_cidade VARCHAR,
    ref_comercial_telefone VARCHAR,
    ref_comercial_contato VARCHAR,
    ref_bancaria_banco VARCHAR,
    ref_bancaria_agencia VARCHAR,
    ref_bancaria_conta VARCHAR,
    bem_imovel_imovel VARCHAR,
    bem_imovel_localizacao VARCHAR,
    bem_imovel_area VARCHAR,
    bem_imovel_valor DOUBLE PRECISION,
    bem_imovel_hipotecado VARCHAR,
    bem_movel_marca VARCHAR,
    bem_movel_modelo VARCHAR,
    bem_movel_alienado VARCHAR,
    animal_especie VARCHAR,
    animal_numero INTEGER,
    animal_consumo_diario DOUBLE PRECISION,
    animal_consumo_mensal DOUBLE PRECISION,
    supervisor_codigo_insumo VARCHAR,
    supervisor_nome_insumo VARCHAR,
    supervisor_codigo_pet VARCHAR,
    supervisor_nome_pet VARCHAR,
    comissao_insumos VARCHAR,
    comissao_pet VARCHAR,
    comissao_observacoes VARCHAR,
    data_criacao TIMESTAMP,
    data_atualizacao TIMESTAMP,
    criado_por VARCHAR,
    atualizado_por VARCHAR,
    tipo_pessoa VARCHAR,
    CONSTRAINT t_cadastro_cliente_v2_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS t_cadastro_produto (
    codigo_supra TEXT,
    status_produto TEXT,
    tipo_giro TEXT,
    estoque_disponivel BIGINT,
    nome_produto TEXT,
    preco DOUBLE PRECISION,
    desconto DOUBLE PRECISION,
    unidade TEXT,
    peso DOUBLE PRECISION,
    cst BIGINT,
    ipi DOUBLE PRECISION,
    icms DOUBLE PRECISION,
    iva_st DOUBLE PRECISION,
    validade_tabela TIMESTAMP,
    preco_lista_supra DOUBLE PRECISION,
    familia INTEGER,
    filhos TEXT,
    marca TEXT,
    fornecedor TEXT,
    data_atualizacao TIMESTAMP,
    preco_anterior DOUBLE PRECISION,
    tipo_alteracao TEXT,
    preco_tonelada_anterior NUMERIC(14,2)
);

CREATE TABLE IF NOT EXISTS t_cadastro_produto_v2 (
    id BIGINT DEFAULT nextval('t_cadastro_produto_v2_id_seq'::regclass) NOT NULL,
    codigo_supra TEXT NOT NULL,
    status_produto TEXT NOT NULL,
    nome_produto TEXT NOT NULL,
    tipo_giro TEXT,
    estoque_disponivel INTEGER,
    unidade TEXT,
    unidade_anterior TEXT,
    peso NUMERIC(12,3),
    peso_bruto NUMERIC(12,3),
    estoque_ideal INTEGER,
    embalagem_venda TEXT,
    unidade_embalagem INTEGER,
    codigo_ean TEXT,
    codigo_embalagem TEXT,
    ncm TEXT,
    fornecedor TEXT,
    filhos INTEGER,
    familia TEXT,
    preco NUMERIC(14,4),
    preco_anterior NUMERIC(14,4),
    preco_tonelada NUMERIC(14,4),
    validade_tabela DATE,
    validade_tabela_anterior DATE,
    desconto_valor_tonelada NUMERIC(14,4),
    data_desconto_inicio DATE,
    data_desconto_fim DATE,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    preco_final NUMERIC(14,2),
    tipo TEXT,
    tipo_alteracao TEXT,
    preco_tonelada_anterior NUMERIC(14,2),
    marca TEXT,
    id_familia INTEGER,
    criado_por VARCHAR,
    atualizado_por VARCHAR,
    status_anterior TEXT,
    CONSTRAINT t_cadastro_produto_v2_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS t_condicoes_pagamento (
    codigo_prazo INTEGER NOT NULL,
    prazo TEXT,
    descricao TEXT,
    custo DOUBLE PRECISION,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    updated_by TEXT,
    CONSTRAINT t_condicoes_pagamento_pkey PRIMARY KEY (codigo_prazo)
);

CREATE TABLE IF NOT EXISTS t_desconto (
    id_desconto INTEGER NOT NULL,
    fator_comissao DOUBLE PRECISION,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    updated_by TEXT,
    CONSTRAINT t_desconto_pkey PRIMARY KEY (id_desconto)
);

CREATE TABLE IF NOT EXISTS t_familia_produtos (
    id INTEGER,
    tipo TEXT,
    familia TEXT,
    marca TEXT,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS t_fornecedor (
    id INTEGER NOT NULL,
    id_fornecedor INTEGER,
    nome_fornecedor VARCHAR(20),
    CONSTRAINT t_fornecedor_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS t_imposto_v2 (
    id BIGINT DEFAULT nextval('t_imposto_v2_id_seq'::regclass) NOT NULL,
    produto_id BIGINT NOT NULL,
    ipi NUMERIC(6,4),
    icms NUMERIC(6,4),
    iva_st NUMERIC(6,4),
    cbs NUMERIC(6,4),
    ibs NUMERIC(6,4),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT t_imposto_v2_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS t_preco_produto_pdf (
    fornecedor TEXT,
    lista TEXT,
    familia TEXT,
    codigo TEXT,
    descricao TEXT,
    preco_ton DOUBLE PRECISION,
    preco_sc DOUBLE PRECISION,
    page BIGINT,
    data_ingestao DATE
);

CREATE TABLE IF NOT EXISTS t_preco_produto_pdf_v2 (
    id BIGINT DEFAULT nextval('t_preco_produto_pdf_v2_id_seq'::regclass) NOT NULL,
    fornecedor VARCHAR(100),
    lista VARCHAR(255),
    familia VARCHAR(255),
    codigo VARCHAR(255) NOT NULL,
    descricao TEXT NOT NULL,
    preco_ton NUMERIC(14,4),
    preco_sc NUMERIC(14,4),
    page INTEGER,
    data_ingestao DATE DEFAULT CURRENT_DATE NOT NULL,
    validade_tabela DATE,
    nome_arquivo TEXT,
    ativo BOOLEAN DEFAULT true NOT NULL,
    usuario TEXT,
    filhos INTEGER,
    CONSTRAINT t_preco_produto_pdf_v2_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS t_usuario (
    id BIGINT NOT NULL,
    nome VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    senha_hash VARCHAR NOT NULL,
    funcao VARCHAR,
    ativo BOOLEAN,
    data_criacao TIMESTAMP,
    data_atualizacao TIMESTAMP,
    criado_por VARCHAR,
    reset_senha_obrigatorio BOOLEAN DEFAULT false,
    email_verificado BOOLEAN DEFAULT false,
    token_verificacao TEXT,
    CONSTRAINT t_usuario_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS tabela_preco_preenchida_v5 (
    id_linha INTEGER,
    id_tabela INTEGER,
    nome_tabela VARCHAR(250),
    fornecedor VARCHAR(250),
    codigo_cliente INTEGER,
    cliente VARCHAR(250),
    codigo_produto_supra VARCHAR(250),
    descricao_produto VARCHAR(250),
    embalagem VARCHAR(250),
    peso_liquido VARCHAR(250),
    valor_produto VARCHAR(250),
    comissao_aplicada INTEGER,
    ajuste_pagamento VARCHAR(250),
    descricao_fator_comissao VARCHAR(250),
    codigo_plano_pagamento VARCHAR(250),
    markup INTEGER,
    valor_final_markup VARCHAR(250),
    valor_s_frete_markup VARCHAR(250),
    valor_frete_aplicado VARCHAR(250),
    frete_kg INTEGER,
    valor_frete VARCHAR(250),
    valor_s_frete VARCHAR(250),
    grupo VARCHAR(250),
    departamento VARCHAR(250),
    ipi INTEGER,
    icms_st INTEGER,
    iva_st INTEGER,
    calcula_st VARCHAR(250),
    ativo VARCHAR(250),
    status_produto VARCHAR(250)
);

CREATE TABLE IF NOT EXISTS tb_background_tasks (
    id INTEGER DEFAULT nextval('tb_background_tasks_id_seq'::regclass) NOT NULL,
    tipo_tarefa VARCHAR(50) NOT NULL,
    referencia_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    tentativas INTEGER NOT NULL,
    erro_msg TEXT,
    criado_em TIMESTAMP DEFAULT now() NOT NULL,
    atualizado_em TIMESTAMP DEFAULT now() NOT NULL,
    CONSTRAINT tb_background_tasks_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS tb_cliente_historico (
    codigo BIGINT,
    nome_empresarial TEXT,
    nome_fantasia TEXT,
    tipo_pessoa TEXT,
    ramo_juridico TEXT,
    atividade_principal TEXT,
    contato_comprador TEXT,
    telefone_contato TEXT,
    email_contato TEXT,
    ativo_nao_ativo TEXT,
    ocorrencia TEXT,
    retira_sim_nao_faturamento TEXT,
    endereco_faturamento TEXT,
    numero_faturamento TEXT,
    bairro_faturamento TEXT,
    cep_faturamento TEXT,
    cidade_faturamento TEXT,
    uf_faturamento TEXT,
    cnpj_cpf_faturamento TEXT,
    inscricao_estadual_faturamento TEXT,
    telefone_faturamento TEXT,
    "e-mail_faturamento" TEXT,
    cidade_entrega TEXT,
    km_entrega DOUBLE PRECISION,
    rota_entrega BIGINT,
    id_entrega BIGINT,
    sugestao_de_frete_to_entrega DOUBLE PRECISION,
    endereco_entrega TEXT,
    observacao_entrega TEXT,
    contato_entrega TEXT,
    telefone_entrega TEXT,
    "e-mail_entrega" TEXT,
    mensagem_faturamento_entrega TEXT,
    mensagem_motorista_entrega TEXT,
    contato_cobranca TEXT,
    telefone_cobranca TEXT,
    email_cobranca TEXT,
    cidade_cobranca TEXT,
    endereco_cobranca TEXT,
    supervisor_alisul TEXT,
    tipo_de_cliente_alisul TEXT,
    data_ocorrencia_alisul DATE,
    observacoes_alisul_1 TEXT,
    observacoes_alisul_2 TEXT,
    bairro_faturamento_formatted TEXT,
    cidade_faturamento_formatted TEXT,
    cnpj_cpf_faturamento_formatted TEXT,
    cidade_entrega_formatted TEXT,
    cidade_cobranca_formatted TEXT,
    email_faturamento TEXT,
    column1 INTEGER
);

CREATE TABLE IF NOT EXISTS tb_idempotency_keys (
    chave VARCHAR(100) NOT NULL,
    id_pedido INTEGER NOT NULL,
    criado_em TIMESTAMP DEFAULT now() NOT NULL,
    CONSTRAINT tb_idempotency_keys_pkey PRIMARY KEY (chave)
);

CREATE TABLE IF NOT EXISTS tb_pedido_link (
    code VARCHAR(32) NOT NULL,
    tabela_id INTEGER NOT NULL,
    com_frete BOOLEAN NOT NULL,
    expires_at TIMESTAMPTZ,
    uses INTEGER DEFAULT 0,
    max_uses INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    data_prevista DATE,
    first_access_at TIMESTAMPTZ,
    last_access_at TIMESTAMPTZ,
    codigo_cliente VARCHAR(80),
    link_url VARCHAR(512),
    criado_por VARCHAR,
    CONSTRAINT tb_pedido_link_pkey PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS tb_pedidos (
    id_pedido BIGINT DEFAULT nextval('tb_pedidos_id_pedido_seq'::regclass) NOT NULL,
    codigo_cliente VARCHAR(80) NOT NULL,
    cliente TEXT NOT NULL,
    contato_nome VARCHAR(120),
    contato_email VARCHAR(160),
    contato_fone VARCHAR(40),
    tabela_preco_id INTEGER NOT NULL,
    validade_ate DATE,
    validade_dias INTEGER,
    data_retirada DATE,
    usar_valor_com_frete BOOLEAN DEFAULT false NOT NULL,
    itens JSONB DEFAULT '[]'::jsonb NOT NULL,
    peso_total_kg NUMERIC(12,3) DEFAULT 0 NOT NULL,
    frete_total NUMERIC(14,2) DEFAULT 0 NOT NULL,
    total_sem_frete NUMERIC(14,2) DEFAULT 0 NOT NULL,
    total_com_frete NUMERIC(14,2) DEFAULT 0 NOT NULL,
    total_pedido NUMERIC(14,2) DEFAULT 0 NOT NULL,
    observacoes VARCHAR(244),
    status VARCHAR(20) DEFAULT 'ABERTO'::character varying NOT NULL,
    confirmado_em TIMESTAMPTZ,
    cancelado_em TIMESTAMPTZ,
    cancelado_motivo VARCHAR(180),
    link_token VARCHAR(64),
    link_url TEXT,
    link_enviado_em TIMESTAMPTZ,
    link_expira_em TIMESTAMPTZ,
    link_primeiro_acesso_em TIMESTAMPTZ,
    link_ultimo_acesso_em TIMESTAMPTZ,
    link_qtd_acessos INTEGER DEFAULT 0 NOT NULL,
    link_status VARCHAR(16) DEFAULT 'PENDENTE'::character varying NOT NULL,
    criado_em TIMESTAMPTZ DEFAULT now() NOT NULL,
    atualizado_em TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_at TIMESTAMPTZ,
    fornecedor TEXT,
    tabela_preco_nome VARCHAR(255),
    atualizado_por VARCHAR(150),
    CONSTRAINT tb_pedidos_pkey PRIMARY KEY (id_pedido)
);

CREATE TABLE IF NOT EXISTS tb_pedidos_itens (
    id_item BIGINT DEFAULT nextval('tb_pedidos_itens_id_item_seq'::regclass) NOT NULL,
    id_pedido BIGINT NOT NULL,
    codigo VARCHAR(80) NOT NULL,
    nome TEXT,
    embalagem TEXT,
    peso_kg NUMERIC(12,3),
    preco_unit NUMERIC(14,2) DEFAULT 0 NOT NULL,
    preco_unit_frt NUMERIC(14,2) DEFAULT 0 NOT NULL,
    quantidade NUMERIC(14,3) DEFAULT 0 NOT NULL,
    subtotal_sem_f NUMERIC(14,2) DEFAULT 0 NOT NULL,
    subtotal_com_f NUMERIC(14,2) DEFAULT 0 NOT NULL,
    condicao_pagamento TEXT,
    tabela_comissao TEXT,
    CONSTRAINT tb_pedidos_itens_pkey PRIMARY KEY (id_item)
);

CREATE TABLE IF NOT EXISTS tb_supervisor (
    codigo_cidade TEXT,
    cidade TEXT,
    uf TEXT,
    nome_supervisor_insumos TEXT,
    numero_supervisor_insumos INTEGER,
    nome_supervisor_pet TEXT,
    numero_supervisor_pet INTEGER,
    tipo_produto TEXT,
    telefone TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS tb_tabela_preco (
    id_linha INTEGER NOT NULL,
    id_tabela INTEGER NOT NULL,
    nome_tabela TEXT NOT NULL,
    fornecedor TEXT NOT NULL,
    codigo_cliente TEXT,
    cliente TEXT NOT NULL,
    codigo_produto_supra TEXT NOT NULL,
    descricao_produto TEXT NOT NULL,
    embalagem TEXT,
    peso_liquido NUMERIC(9,3) NOT NULL,
    valor_produto NUMERIC(14,2) NOT NULL,
    comissao_aplicada NUMERIC(9,4) DEFAULT 0 NOT NULL,
    ajuste_pagamento NUMERIC(14,2) DEFAULT 0 NOT NULL,
    descricao_fator_comissao TEXT NOT NULL,
    codigo_plano_pagamento TEXT NOT NULL,
    valor_frete_aplicado NUMERIC(9,4) DEFAULT 0 NOT NULL,
    frete_kg NUMERIC(9,3) DEFAULT 0 NOT NULL,
    valor_liquido NUMERIC(14,2),
    valor_frete NUMERIC(14,2) NOT NULL,
    valor_s_frete NUMERIC(14,2) NOT NULL,
    grupo TEXT,
    departamento TEXT,
    ipi NUMERIC(9,4) NOT NULL,
    icms_st NUMERIC(9,4) NOT NULL,
    iva_st NUMERIC(9,4) NOT NULL,
    ativo BOOLEAN DEFAULT true NOT NULL,
    criado_em TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text),
    editado_em TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text),
    deletado_em TIMESTAMP,
    criacao_usuario TEXT,
    alteracao_usuario TEXT,
    calcula_st BOOLEAN DEFAULT false NOT NULL,
    markup NUMERIC(9,3),
    valor_final_markup NUMERIC(14,2),
    valor_s_frete_markup NUMERIC(14,2),
    CONSTRAINT tb_tabela_preco_pkey PRIMARY KEY (id_linha)
);

CREATE TABLE IF NOT EXISTS tb_tabela_preco_old (
    id_linha INTEGER NOT NULL,
    nome_tabela TEXT NOT NULL,
    validade_inicio DATE NOT NULL,
    validade_fim DATE NOT NULL,
    fornecedor TEXT NOT NULL,
    cliente TEXT NOT NULL,
    codigo_tabela TEXT NOT NULL,
    descricao TEXT NOT NULL,
    embalagem TEXT,
    peso_liquido DOUBLE PRECISION,
    peso_bruto DOUBLE PRECISION,
    valor DOUBLE PRECISION NOT NULL,
    comissao_aplicada DOUBLE PRECISION DEFAULT 0.0,
    ajuste_pagamento DOUBLE PRECISION DEFAULT 0.0,
    fator_comissao DOUBLE PRECISION,
    plano_pagamento TEXT,
    frete_percentual DOUBLE PRECISION,
    frete_kg DOUBLE PRECISION,
    valor_liquido DOUBLE PRECISION,
    grupo TEXT,
    departamento TEXT,
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text),
    editado_em TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text),
    deletado_em TIMESTAMP,
    id_tabela INTEGER,
    ipi DOUBLE PRECISION,
    iva_st DOUBLE PRECISION,
    CONSTRAINT tb_tabela_preco_old_pkey PRIMARY KEY (id_linha)
);


-- Views

-- NOTE: 'v_produto_v2_preco' is a VIEW in dev. Recreate manually if needed.
-- It depends on: t_cadastro_produto_v2 and t_imposto_v2
CREATE OR REPLACE VIEW v_produto_v2_preco AS
SELECT
    p.id, p.codigo_supra, p.nome_produto, p.embalagem_venda,
    p.peso, p.peso_bruto, p.preco, p.preco_anterior,
    p.preco_tonelada, p.preco_tonelada_anterior, p.marca,
    p.familia, p.id_familia, p.fornecedor, p.tipo,
    p.validade_tabela, p.validade_tabela_anterior,
    p.status_produto, p.unidade, p.unidade_anterior, p.tipo_giro,
    p.estoque_disponivel, p.estoque_ideal, p.unidade_embalagem,
    p.codigo_ean, p.codigo_embalagem, p.ncm, p.filhos,
    p.desconto_valor_tonelada, p.data_desconto_inicio, p.data_desconto_fim,
    i.ipi, i.iva_st, i.icms, i.cbs, i.ibs
FROM t_cadastro_produto_v2 p
LEFT JOIN t_imposto_v2 i ON i.produto_id = p.id;

-- NOTE: 'vw_condicao_pagto_mais_utilizada' is a VIEW in dev. Recreate manually if needed.
-- It depends on: t_cadastro_produto_v2 and t_imposto_v2
CREATE OR REPLACE VIEW vw_condicao_pagto_mais_utilizada AS
SELECT
    t.codigo_cliente::INTEGER AS "codigo tratado",
    t.cliente AS "Cliente",
    t.codigo_plano_pagamento AS "Cond. Pagto Mais Utilizada",
    COUNT(*) AS total_ocorrencias
FROM tb_tabela_preco t
GROUP BY t.codigo_cliente, t.cliente, t.codigo_plano_pagamento
ORDER BY total_ocorrencias DESC;


-- Foreign Key Constraints

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name='tb_pedidos_itens_id_pedido_fkey' AND table_schema='public'
  ) THEN
    ALTER TABLE tb_pedidos_itens ADD CONSTRAINT tb_pedidos_itens_id_pedido_fkey
      FOREIGN KEY (id_pedido) REFERENCES tb_pedidos(id_pedido)
      ON UPDATE NO ACTION ON DELETE CASCADE;
  END IF;
END $$;


-- Unique Constraints

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name='uq_lista_precos_chave' AND table_schema='public'
  ) THEN
    ALTER TABLE lista_precos ADD CONSTRAINT uq_lista_precos_chave UNIQUE (fornecedor, lista, codigo, descricao);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name='ux_produto_v2_fornec_tipo_codigo' AND table_schema='public'
  ) THEN
    ALTER TABLE t_cadastro_produto_v2 ADD CONSTRAINT ux_produto_v2_fornec_tipo_codigo UNIQUE (fornecedor, tipo, codigo_supra);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name='uq_tb_preco__tabela_prod' AND table_schema='public'
  ) THEN
    ALTER TABLE tb_tabela_preco ADD CONSTRAINT uq_tb_preco__tabela_prod UNIQUE (id_tabela, codigo_produto_supra);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name='uq_tb_preco_item' AND table_schema='public'
  ) THEN
    ALTER TABLE tb_tabela_preco ADD CONSTRAINT uq_tb_preco_item UNIQUE (id_tabela, codigo_produto_supra);
  END IF;
END $$;


-- Indexes

CREATE UNIQUE INDEX IF NOT EXISTS uq_lista_precos_chave ON public.lista_precos USING btree (fornecedor, lista, codigo, descricao);

CREATE INDEX IF NOT EXISTS idx_pedido_status__codigo ON public.pedido_status USING btree (codigo);

CREATE INDEX IF NOT EXISTS idx_pedido_status__ordem ON public.pedido_status USING btree (ordem);

CREATE INDEX IF NOT EXISTS ix_t_cadastro_cliente_v2_id ON public.t_cadastro_cliente_v2 USING btree (id);

CREATE INDEX IF NOT EXISTS idx_produto_v2_familia ON public.t_cadastro_produto_v2 USING btree (familia);

CREATE INDEX IF NOT EXISTS idx_produto_v2_status ON public.t_cadastro_produto_v2 USING btree (status_produto);

CREATE UNIQUE INDEX IF NOT EXISTS ux_produto_v2_fornec_tipo_codigo ON public.t_cadastro_produto_v2 USING btree (fornecedor, tipo, codigo_supra);

CREATE UNIQUE INDEX IF NOT EXISTS tb_condicoes_pagamento_pkey ON public.t_condicoes_pagamento USING btree (codigo_prazo);

CREATE UNIQUE INDEX IF NOT EXISTS tb_desconto_pkey ON public.t_desconto USING btree (id_desconto);

CREATE INDEX IF NOT EXISTS idx_preco_pdf_v2_lista_fornecedor ON public.t_preco_produto_pdf_v2 USING btree (lista, fornecedor, codigo);

CREATE UNIQUE INDEX IF NOT EXISTS ix_t_usuario_email ON public.t_usuario USING btree (email);

CREATE INDEX IF NOT EXISTS ix_t_usuario_id ON public.t_usuario USING btree (id);

CREATE INDEX IF NOT EXISTS ix_tb_background_tasks_id ON public.tb_background_tasks USING btree (id);

CREATE INDEX IF NOT EXISTS ix_tb_idempotency_keys_chave ON public.tb_idempotency_keys USING btree (chave);

CREATE INDEX IF NOT EXISTS ix_tb_pedido_link_link_url ON public.tb_pedido_link USING btree (link_url);

CREATE INDEX IF NOT EXISTS idx_pedidos_abertos_criado ON public.tb_pedidos USING btree (criado_em DESC) WHERE ((status)::text = 'ABERTO'::text);

CREATE INDEX IF NOT EXISTS idx_pedidos_codigo_cliente ON public.tb_pedidos USING btree (codigo_cliente);

CREATE INDEX IF NOT EXISTS idx_pedidos_itens_gin ON public.tb_pedidos USING gin (itens jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_pedidos_link_expira ON public.tb_pedidos USING btree (link_expira_em) WHERE ((link_status)::text = ANY (ARRAY[('ENVIADO'::character varying)::text, ('ABERTO'::character varying)::text]));

CREATE INDEX IF NOT EXISTS idx_pedidos_link_status ON public.tb_pedidos USING btree (link_status);

CREATE INDEX IF NOT EXISTS idx_pedidos_status ON public.tb_pedidos USING btree (status);

CREATE INDEX IF NOT EXISTS idx_pedidos_tabela ON public.tb_pedidos USING btree (tabela_preco_id);

CREATE INDEX IF NOT EXISTS ix_tb_pedidos_created_at ON public.tb_pedidos USING btree (created_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pedidos_link_token ON public.tb_pedidos USING btree (link_token) WHERE (link_token IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_pedidos_itens_pedido ON public.tb_pedidos_itens USING btree (id_pedido);

CREATE UNIQUE INDEX IF NOT EXISTS tb_tabela_preco_v2_pkey ON public.tb_tabela_preco USING btree (id_linha);

CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_preco__tabela_prod ON public.tb_tabela_preco USING btree (id_tabela, codigo_produto_supra);

CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_preco_item ON public.tb_tabela_preco USING btree (id_tabela, codigo_produto_supra);

CREATE INDEX IF NOT EXISTS idx_tb_tabela_preco_id_tabela ON public.tb_tabela_preco_old USING btree (id_tabela);