
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, BigInteger, Sequence
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class ClienteModelV2(Base):
    __tablename__ = "t_cadastro_cliente_v2"

    id = Column(BigInteger, Sequence('cliente_v2_id_seq'), primary_key=True, index=True, autoincrement=True)
    
    # 1. CadastroCliente
    cadastro_codigo_da_empresa = Column(String)
    cadastro_ativo = Column(Boolean)
    cadastro_tipo_cliente = Column(String)
    cadastro_tipo_venda = Column(String)
    cadastro_tipo_compra = Column(String)
    cadastro_limite_credito = Column(Float)
    cadastro_nome_cliente = Column(String)
    cadastro_nome_fantasia = Column(String)
    cadastro_cnpj = Column(String)
    cadastro_inscricao_estadual = Column(String)
    cadastro_cpf = Column(String)
    cadastro_situacao = Column(String)
    # JSONB: lista de strings com até 5 indicações. Ex: ["Fulano", "Ciclano"]
    cadastro_indicacao_cliente = Column(JSONB, default=list)
    cadastro_ramo_de_atividade = Column(String)
    cadastro_atividade_principal = Column(String)
    cadastro_markup = Column(Float, default=0.0) # Markup % (ex: 10.5 para 10.5%)
    cadastro_periodo_de_compra = Column(String)
    tipo_pessoa = Column(String) # [NEW] Added for client type differentiation

    # 2. ResponsavelCompras
    compras_nome_responsavel = Column(String)
    compras_celular_responsavel = Column(String)
    compras_telefone_fixo_responsavel = Column(String)
    compras_email_resposavel = Column(String)
    compras_data_nascimento_resposavel = Column(String)
    compras_observacoes_responsavel = Column(String)
    compras_filial_resposavel = Column(String)

    # 3. EnderecoFaturamento
    faturamento_endereco = Column(String)
    faturamento_bairro = Column(String)
    faturamento_cep = Column(String)
    faturamento_localizacao = Column(String)
    faturamento_municipio = Column(String)
    faturamento_estado = Column(String)
    faturamento_email_danfe = Column(String)

    # 4. RepresentanteLegal
    legal_nome = Column(String)
    legal_celular = Column(String)
    legal_email = Column(String)
    legal_data_nascimento = Column(String)
    legal_observacoes = Column(String)

    # 5. EnderecoEntrega
    entrega_endereco = Column(String)
    entrega_bairro = Column(String)
    entrega_cep = Column(String)
    entrega_localizacao = Column(String)
    entrega_municipio = Column(String)
    entrega_estado = Column(String)
    entrega_rota_principal = Column(String)
    entrega_rota_aproximacao = Column(String)
    entrega_observacao_motorista = Column(String)

    # 6. ResponsavelRecebimento
    recebimento_nome = Column(String)
    recebimento_celular = Column(String)
    recebimento_email = Column(String)
    recebimento_data_nascimento = Column(String)
    recebimento_observacoes = Column(String)

    # 7. EnderecoCobranca
    cobranca_endereco = Column(String)
    cobranca_bairro = Column(String)
    cobranca_cep = Column(String)
    cobranca_localizacao = Column(String)
    cobranca_municipio = Column(String)
    cobranca_estado = Column(String)

    # 8. ResponsavelCobranca
    cobranca_resp_nome = Column(String)
    cobranca_resp_celular = Column(String)
    cobranca_resp_email = Column(String)
    cobranca_resp_data_nascimento = Column(String)
    cobranca_resp_observacoes = Column(String)

    # 9. DadosUltimasCompras
    ultimas_compras_numero_danfe = Column(String)
    ultimas_compras_emissao = Column(String)
    ultimas_compras_valor_total = Column(Float)
    ultimas_compras_valor_frete = Column(Float)
    ultimas_compras_valor_frete_padrao = Column(Float)
    ultimas_compras_valor_ultimo_frete = Column(Float)
    ultimas_compras_lista_tabela = Column(String)
    ultimas_compras_condicoes_pagamento = Column(String)
    ultimas_compras_cliente_calcula_st = Column(String)
    ultimas_compras_prazo_medio = Column(String)
    ultimas_compras_previsao_proxima = Column(String)
    
    # 10. ObservacoesNaoCompra
    obs_nao_compra_observacoes = Column(String)

    # 11. DadosElaboracaoCadastro
    elaboracao_classificacao = Column(String)
    elaboracao_tipo_venda = Column(String)
    elaboracao_limite_credito = Column(Float)
    elaboracao_data_vencimento = Column(String)
    elaboracao_vendedor = Column(String)

    # 12. GrupoEconomico — JSONB: lista com até 3 grupos. Ex: [{"codigo": "G1", "nome": "Grupo X"}]
    grupos_economicos = Column(JSONB, default=list)

    # 13. ReferenciaComercial — JSONB: lista com até 3 refs. Ex: [{"empresa": "X", "cidade": "Y", "telefone": "Z", "contato": "W"}]
    referencias_comerciais = Column(JSONB, default=list)

    # 14. ReferenciaBancaria — JSONB: lista com até 3 refs. Ex: [{"banco": "X", "agencia": "Y", "conta_corrente": "Z", "gerente": "W", "contato_gerente": "K"}]
    referencias_bancarias = Column(JSONB, default=list)

    # 15. BemImovel — JSONB: lista com até 3 bens. Ex: [{"imovel": "X", "localizacao": "Y", "area": "Z", "valor": 100.0, "hipotecado": "Sim"}]
    bens_imoveis = Column(JSONB, default=list)

    # 16. BemMovel — JSONB: lista com até 3 bens. Ex: [{"marca": "X", "modelo": "Y", "alienado": "Sim"}]
    bens_moveis = Column(JSONB, default=list)

    # 17. PlantelAnimal — JSONB: lista com até 3 plantéis. Ex: [{"especie": "X", "numero": 10, "consumo_diario": 5.0, "consumo_mensal": 150.0}]
    planteis_animais = Column(JSONB, default=list)

    # 18. Supervisores
    supervisor_codigo_insumo = Column(String)
    supervisor_nome_insumo = Column(String)
    supervisor_codigo_pet = Column(String)
    supervisor_nome_pet = Column(String)

    # 19. ComissaoDispet
    comissao_insumos = Column(String)
    comissao_pet = Column(String)
    comissao_observacoes = Column(String)

    # 20. CanalVenda
    canal_pet     = Column(String)
    canal_frost   = Column(String)
    canal_insumos = Column(String)

    # Meta
    data_criacao = Column(DateTime)
    data_atualizacao = Column(DateTime)

    criado_por = Column(String, nullable=True)
    atualizado_por = Column(String, nullable=True)
