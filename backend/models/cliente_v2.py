
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, BigInteger, Sequence
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
    cadastro_indicacao_cliente = Column(String)
    cadastro_ramo_de_atividade = Column(String)
    cadastro_atividade_principal = Column(String)

    # 2. ResponsavelCompras
    compras_nome_responsavel = Column(String)
    compras_celular_responsavel = Column(String)
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

    # 12. GrupoEconomico
    grupo_economico_codigo = Column(String)
    grupo_economico_nome = Column(String)

    # 13. ReferenciaComercial
    ref_comercial_empresa = Column(String)
    ref_comercial_cidade = Column(String)
    ref_comercial_telefone = Column(String)
    ref_comercial_contato = Column(String)

    # 14. ReferenciaBancaria
    ref_bancaria_banco = Column(String)
    ref_bancaria_agencia = Column(String)
    ref_bancaria_conta = Column(String)

    # 15. BemImovel
    bem_imovel_imovel = Column(String)
    bem_imovel_localizacao = Column(String)
    bem_imovel_area = Column(String)
    bem_imovel_valor = Column(Float)
    bem_imovel_hipotecado = Column(String)

    # 16. BemMovel
    bem_movel_marca = Column(String)
    bem_movel_modelo = Column(String)
    bem_movel_alienado = Column(String)

    # 17. PlantelAnimal
    animal_especie = Column(String)
    animal_numero = Column(Integer)
    animal_consumo_diario = Column(Float)
    animal_consumo_mensal = Column(Float)

    # 18. Supervisores
    supervisor_codigo_insumo = Column(String)
    supervisor_nome_insumo = Column(String)
    supervisor_codigo_pet = Column(String)
    supervisor_nome_pet = Column(String)

    # 19. ComissaoDispet
    comissao_insumos = Column(String)
    comissao_pet = Column(String)
    comissao_observacoes = Column(String)

    # Meta
    data_criacao = Column(DateTime)
    data_atualizacao = Column(DateTime)

    criado_por = Column(String, nullable=True)
    atualizado_por = Column(String, nullable=True)
