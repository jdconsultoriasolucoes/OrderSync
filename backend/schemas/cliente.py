from pydantic import BaseModel , Field #, field_validator, model_validator, FieldValidationInfo, model_validator
from typing import Optional, List
from datetime import datetime

#from backend.utils.validators import (
#validar_cpf_valido,
#    validar_cnpj_valido,
#    validar_email,
#    validar_documento_por_tipo_pessoa,
#    validar_data_nascimento,
#    validar_data_vencimento,
#    validar_emissao,
#    validar_valor_positivo,
#    validar_consumo_coerente
#)

# Classes de Cadastro de Clientes

class CadastroCliente(BaseModel):
    id: int
    codigo_da_empresa: Optional[str]
    ativo: Optional[bool]
    tipo_cliente: Optional[str]
    tipo_venda: Optional[str]
    tipo_compra: Optional[str]
    limite_credito: Optional[float]
    nome_cliente: str
    nome_fantasia: Optional[str]
    cnpj: Optional[str]
    inscricao_estadual: Optional[str]
    cpf: Optional[str]
    situacao: Optional[str]
    indicacao_cliente: Optional[str]
    ramo_de_atividade: Optional[str]
    atividade_principal: Optional[str]

#    @field_validator("cpf")
#    def cpf_valido(cls, v):
#        if v and not validar_cpf_valido(v):
#            raise ValueError("CPF inválido")
#        return v

#    @field_validator("cnpj")
#    def cnpj_valido(cls, v):
#        if v and not validar_cnpj_valido(v):
#            raise ValueError("CNPJ inválido")
#        return v
    
    # Validação cruzada: CPF ou CNPJ obrigatório conforme tipo
#    @model_validator(mode="after")
#    def validar_documento(self):
#        if not validar_documento_por_tipo_pessoa(self.tipo_cliente, self.cpf, self.cnpj):
#            raise ValueError("CPF ou CNPJ obrigatório conforme tipo de cliente")
#        return self

class ResponsavelCompras(BaseModel):
    nome_responsavel: Optional[str]
    celular_responsavel: Optional[str]
    email_resposavel: Optional[str]
    data_nascimento_resposavel: Optional[str]
    observacoes_responsavel: Optional[str]
    filial_resposavel: Optional[str]

#    @field_validator("email_resposavel")
#    def email_valido(cls, v):
#        if v and not validar_email(v):
#            raise ValueError("Email inválido")
#        return v

#    @field_validator("data_nascimento_resposavel")
#    def nascimento_valido(cls, v):
#        if v and not validar_data_nascimento(v):
#            raise ValueError("Data de nascimento inválida")
#        return v

# Classes de Endereço de Faturamento

class EnderecoFaturamento(BaseModel):
    endereco_faturamento: Optional[str]
    bairro_faturamento: Optional[str]
    cep_faturamento: Optional[str]
    localizacao_faturamento: Optional[str]
    municipio_faturamento: Optional[str]
    estado_faturamento: Optional[str]
    email_danfe_faturamento: Optional[str]

#    @field_validator("email_danfe_faturamento")
#    def email_valido(cls, v):
#        if v and not validar_email(v):
#            raise ValueError("Email inválido")
#        return v

class RepresentanteLegal(BaseModel):
    nome_RepresentanteLegal: Optional[str]
    celular_RepresentanteLegal: Optional[str]
    email_RepresentanteLegal: Optional[str]
    data_nascimento_RepresentanteLegal: Optional[str]
    observacoes_RepresentanteLegal: Optional[str]
    
#    @field_validator("email_RepresentanteLegal")
#    def email_valido(cls, v):
#        if v and not validar_email(v):
#            raise ValueError("Email inválido")
#        return v

#    @field_validator("data_nascimento_RepresentanteLegal")
#    def nascimento_valido(cls, v):
#        if v and not validar_data_nascimento(v):
#            raise ValueError("Data de nascimento inválida")
#        return v

# Classes de Endereço de Entrega

class EnderecoEntrega(BaseModel):
    endereco_EnderecoEntrega: Optional[str]
    bairro_EnderecoEntrega: Optional[str]
    cep_EnderecoEntrega: Optional[str]
    localizacao_EnderecoEntrega: Optional[str]
    municipio_EnderecoEntrega: Optional[str]
    estado_EnderecoEntrega: Optional[str]
    rota_principal_EnderecoEntrega: Optional[str]
    rota_de_aproximacao_EnderecoEntrega: Optional[str]
    observacao_motorista_EnderecoEntrega: Optional[str]

class ResponsavelRecebimento(BaseModel):
    nome_ResponsavelRecebimento: Optional[str]
    celular_ResponsavelRecebimento: Optional[str]
    email_ResponsavelRecebimento: Optional[str]
    data_nascimento_ResponsavelRecebimento: Optional[str]
    observacoes_ResponsavelRecebimento: Optional[str]


#    @field_validator("email_ResponsavelRecebimento")
#    def email_valido(cls, v):
#        if v and not validar_email(v):
#            raise ValueError("Email inválido")
#        return v

#    @field_validator("data_nascimento_ResponsavelRecebimento")
#    def nascimento_valido(cls, v):
#        if v and not validar_data_nascimento(v):
#            raise ValueError("Data de nascimento inválida")
#        return v



# Classes de Endereço de Cobrança

class EnderecoCobranca(BaseModel):
    endereco_EnderecoCobranca: Optional[str]
    bairro_EnderecoCobranca: Optional[str]
    cep_EnderecoCobranca: Optional[str]
    localizacao_EnderecoCobranca: Optional[str]
    municipio_EnderecoCobranca: Optional[str]
    estado_EnderecoCobranca: Optional[str]

class ResponsavelCobranca(BaseModel):
    nome_ResponsavelCobranca: Optional[str]
    celular_ResponsavelCobranca: Optional[str]
    email_ResponsavelCobranca: Optional[str]
    data_nascimento_ResponsavelCobranca: Optional[str]
    observacoes_ResponsavelCobranca: Optional[str]


#    @field_validator("email_ResponsavelCobranca")
#    def email_valido(cls, v):
#        if v and not validar_email(v):
#            raise ValueError("Email inválido")
#        return v

#    @field_validator("data_nascimento_ResponsavelCobranca")
#    def nascimento_valido(cls, v):
#        if v and not validar_data_nascimento(v):
#            raise ValueError("Data de nascimento inválida")
#        return v

# Classes de Compras

class DadosUltimasCompras(BaseModel):
    numero_danfe_Compras: Optional[str]
    emissao_Compras: Optional[str]
    valor_total_Compras: Optional[float]
    valor_frete_Compras: Optional[float]
    valor_frete_padrao_Compras: Optional[float]
    valor_ultimo_frete_to_Compras: Optional[float]
    lista_tabela_Compras: Optional[str]
    condicoes_pagamento_Compras: Optional[str]
    cliente_calcula_st_Compras: Optional[str]
    prazo_medio_compra_Compras: Optional[str]
    previsao_proxima_compra_Compras: Optional[str]

#    @field_validator("emissao_Compras")
#    def data_emissao_valida(cls, v):
#        if v and not validar_emissao(v):
#            raise ValueError("Data de emissão inválida (futura)")
#        return v

#    @field_validator(
#        "valor_total_Compras",
#        "valor_frete_Compras",
#        "valor_frete_padrao_Compras",
#        "valor_ultimo_frete_to_Compras"
#    )
#    def valores_positivos(cls, v):
#        if v is not None and not validar_valor_positivo(v):
#            raise ValueError("Valor não pode ser negativo")
#        return v

class ObservacoesNaoCompra(BaseModel):
    observacoes_Compras: Optional[str]

# Classes de Elaboração do Cadastro

class DadosElaboracaoCadastro(BaseModel):
    classificacao_ElaboracaoCadastro: Optional[str]
    tipo_venda_prazo_ou_vista_ElaboracaoCadastro: Optional[str]
    limite_credito_ElaboracaoCadastro: Optional[float]
    data_vencimento_ElaboracaoCadastro: Optional[str]

#    @field_validator("data_vencimento_ElaboracaoCadastro")
#    def vencimento_valido(cls, v):
#        if v and not validar_data_vencimento(v):
#            raise ValueError("Data de vencimento inválida (no passado)")
#        return v

#    @field_validator("limite_credito_ElaboracaoCadastro")
#    def limite_credito_valido(cls, v):
#        if v is not None and not validar_valor_positivo(v):
#            raise ValueError("Limite de crédito não pode ser negativo")
#        return v

class GrupoEconomico(BaseModel):
    codigo_ElaboracaoCadastro: Optional[str]
    nome_empresarial_ElaboracaoCadastro: Optional[str]

class ReferenciaComercial(BaseModel):
    empresa_ElaboracaoCadastro: Optional[str]
    cidade_ElaboracaoCadastro: Optional[str]
    telefone_ElaboracaoCadastro: Optional[str]
    contato_ElaboracaoCadastro: Optional[str]

class ReferenciaBancaria(BaseModel):
    banco_ElaboracaoCadastro: Optional[str]
    agencia_ElaboracaoCadastro: Optional[str]
    conta_corrente_ElaboracaoCadastro: Optional[str]

class BemImovel(BaseModel):
    imovel_ElaboracaoCadastro: Optional[str]
    localizacao_ElaboracaoCadastro: Optional[str]
    area_ElaboracaoCadastro: Optional[str]
    valor_ElaboracaoCadastro: Optional[float]
    hipotecado_ElaboracaoCadastro: Optional[str]

class BemMovel(BaseModel):
    marca_ElaboracaoCadastro: Optional[str]
    modelo_ElaboracaoCadastro: Optional[str]
    alienado_ElaboracaoCadastro: Optional[str]

class PlantelAnimal(BaseModel):
    especie_ElaboracaoCadastro: Optional[str]
    numero_de_animais_ElaboracaoCadastro: Optional[int]
    consumo_diario_ElaboracaoCadastro: Optional[float]
    consumo_mensal_ElaboracaoCadastro: Optional[float]    

#@model_validator(mode="after")
#def validar_consumo_animal(cls, values):
    # lógica permanece a mesma
#    return values

class Supervisores(BaseModel):
    codigo_insumo_ElaboracaoCadastro: Optional[str]
    nome_insumos_ElaboracaoCadastro: Optional[str]
    codigo_pet_ElaboracaoCadastro: Optional[str]
    nome_pet_ElaboracaoCadastro: Optional[str]

class ComissaoDispet(BaseModel):
    insumos_ElaboracaoCadastro: Optional[str]
    pet_ElaboracaoCadastro: Optional[str]
    observacoes_ElaboracaoCadastro: Optional[str]



class ClienteCompleto(BaseModel):
    cadastrocliente: CadastroCliente
    responsavel_compras: Optional[ResponsavelCompras] = None
    endereco_faturamento: Optional[EnderecoFaturamento] = None
    representante_legal: Optional[RepresentanteLegal] = None
    endereco_entrega: Optional[EnderecoEntrega] = None
    responsavel_recebimento: Optional[ResponsavelRecebimento] = None
    endereco_cobranca: Optional[EnderecoCobranca] = None
    responsavel_cobranca: Optional[ResponsavelCobranca] = None
    dados_ultimas_compras: Optional[DadosUltimasCompras] = None
    observacoes_nao_compra: Optional[ObservacoesNaoCompra] = None
    dados_elaboracao_cadastro: Optional[DadosElaboracaoCadastro] = None
    grupo_economico: Optional[GrupoEconomico] = None
    referencia_comercial: Optional[ReferenciaComercial] = None
    referencia_bancaria: Optional[ReferenciaBancaria] = None
    bem_imovel: Optional[BemImovel] = None
    bem_movel: Optional[BemMovel] = None
    plantel_animal: Optional[PlantelAnimal] = None
    supervisores: Optional[Supervisores] = None
    comissao_dispet: Optional[ComissaoDispet] = None

class ClienteResumo(BaseModel):
    id: int
    nome: Optional[str]
    cpf: Optional[str]
    cnpj: Optional[str]
    email: Optional[str]
    estado: Optional[str]
    ativo: Optional[bool]