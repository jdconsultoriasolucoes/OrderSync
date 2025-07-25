from sqlalchemy import Column, String, Boolean, Float, DateTime, Integer
from db.database import Base

class ClienteModel(Base):
    __tablename__ = "tb_cadastro_cliente"

    id = Column(Integer, primary_key=True, index=True)
    codigo_da_empresa = Column(String)
    ativo = Column(Boolean)
    tipo_cliente = Column(String)
    tipo_venda = Column(String)
    tipo_compra = Column(String)
    limite_credito = Column(Float)
    nome_cliente = Column(String)
    nome_fantasia = Column(String)
    cnpj = Column(String)
    inscricao_estadual = Column(String)
    cpf = Column(String)
    situacao = Column(String)
    indicacao_cliente = Column(String)
    ramo_de_atividade = Column(String)
    atividade_principal = Column(String)

    nome_responsavel_compras = Column(String)
    celular_responsavel_compras = Column(String)
    email_responsavel_compras = Column(String)
    data_nascimento_responsavel_compras = Column(DateTime)
    observacoes_responsavel_compras = Column(String)
    filial_responsavel_compras = Column(String)

    endereco_faturamento = Column(String)
    bairro_faturamento = Column(String)
    cep_faturamento = Column(String)
    localizacao_faturamento = Column(String)
    municipio_faturamento = Column(String)
    estado_faturamento = Column(String)
    email_danfe_faturamento = Column(String)

    nome_representante_legal = Column(String)
    celular_representante_legal = Column(String)
    email_representante_legal = Column(String)
    data_nascimento_representante_legal = Column(DateTime)
    observacoes_representante_legal = Column(String)

    endereco_entrega = Column(String)
    bairro_endereco_entrega = Column(String)
    cep_endereco_entrega = Column(String)
    localizacao_endereco_entrega = Column(String)
    municipio_endereco_entrega = Column(String)
    estado_endereco_entrega = Column(String)
    rota_principal_endereco_entrega = Column(String)
    rota_aproximacao_endereco_entrega = Column(String)
    observacao_motorista_endereco_entrega = Column(String)

    nome_responsavel_recebimento = Column(String)
    celular_responsavel_recebimento = Column(String)
    email_responsavel_recebimento = Column(String)
    data_nascimento_responsavel_recebimento = Column(DateTime)
    observacoes_responsavel_recebimento = Column(String)

    endereco_cobranca = Column(String)
    bairro_endereco_cobranca = Column(String)
    cep_endereco_cobranca = Column(String)
    localizacao_endereco_cobranca = Column(String)
    municipio_endereco_cobranca = Column(String)
    estado_endereco_cobranca = Column(String)

    nome_responsavel_cobranca = Column(String)
    celular_responsavel_cobranca = Column(String)
    email_responsavel_cobranca = Column(String)
    data_nascimento_responsavel_cobranca = Column(DateTime)
    observacoes_responsavel_cobranca = Column(String)


#    numero_danfe_Compras = Column(String)
#    emissao_Compras = Column(String)
#    valor_total_Compras = Column(Float)
#    valor_frete_Compras = Column(Float)
#    valor_frete_padrao_Compras = Column(Float)
#    valor_ultimo_frete_to_Compras = Column(Float)
#    lista_tabela_Compras = Column(String)
#    condicoes_pagamento_Compras = Column(String)
#    cliente_calcula_st_Compras = Column(String)
#    prazo_medio_compra_Compras = Column(String)
#    previsao_proxima_compra_Compras = Column(String)

#    observacoes_Compras = Column(String)

    classificacao_elaboracao_cadastro = Column(String)
    tipo_venda_elaboracao_cadastro = Column(String)
    limite_credito_elaboracao_cadastro = Column(Float)
    data_vencimento_elaboracao_cadastro = Column(DateTime)

    codigo_elaboracao_cadastro = Column(String)
    nome_empresarial_elaboracao_cadastro = Column(String)

    empresa_elaboracao_cadastro = Column(String)
    cidade_elaboracao_cadastro = Column(String)
    telefone_elaboracao_cadastro = Column(String)
    contato_elaboracao_cadastro = Column(String)

    banco_elaboracao_cadastro = Column(String)
    agencia_elaboracao_cadastro = Column(String)
    conta_corrente_elaboracao_cadastro = Column(String)

    imovel_elaboracao_cadastro = Column(String)
    localizacao_elaboracao_cadastro = Column(String)
    area_elaboracao_cadastro = Column(String)
    valor_elaboracao_cadastro = Column(Float)
    hipotecado_elaboracao_cadastro = Column(String)

    bens_moveis_marca_elaboracao_cadastro = Column(String)
    bens_moveis_modelo_elaboracao_cadastro = Column(String)
    bens_moveis_alienado_elaboracao_cadastro = Column(String)

    especie_animal_elaboracao_cadastro = Column(String)
    numero_de_animais_elaboracao_cadastro = Column(String)
    consumo_diario_kg_elaboracao_cadastro = Column(Float)
    consumo_mensal_kg_elaboracao_cadastro = Column(Float)

    codigo_insumo_elaboracao_cadastro = Column(String)
    nome_insumo_elaboracao_cadastro = Column(String)
    codigo_pet_elaboracao_cadastro = Column(String)
    nome_pet_elaboracao_cadastro = Column(String)

    insumos_elaboracao_cadastro = Column(String)
    pet_elaboracao_cadastro = Column(String)
    observacoes_elaboracao_cadastro = Column(String)

    data_criacao = Column(DateTime)
    data_atualizacao = Column(DateTime)
