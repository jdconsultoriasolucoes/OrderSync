from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from utils.validators import (
    validar_cpf_valido,
    validar_cnpj_valido,
    validar_email,
    validar_data_nascimento,
    validar_data_vencimento,
    validar_emissao,
    validar_valor_positivo,
    validar_consumo_coerente
)
from pydantic import field_validator, model_validator

# Classes de Cadastro de Clientes

class CadastroCliente(BaseModel):
    id: int
    codigo_da_empresa: Optional[str] = None
    ativo: Optional[bool] = None
    tipo_pessoa: Optional[str] = None
    tipo_cliente: Optional[str] = None
    tipo_venda: Optional[str] = None
    tipo_compra: Optional[str] = None
    limite_credito: Optional[float] = None
    nome_cliente: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    cpf: Optional[str] = None
    situacao: Optional[str] = None
    indicacao_cliente: Optional[str] = None
    ramo_de_atividade: Optional[str] = None
    atividade_principal: Optional[str] = None
    cadastro_markup: Optional[float] = 0.0
    periodo_de_compra: Optional[str] = None

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, v):
        if v and str(v).strip() and not validar_cpf_valido(v):
            # Log ou tratamento silencioso aqui se desejar
            return v
        return v

    @field_validator("cnpj")
    @classmethod
    def cnpj_valido(cls, v):
        if v and str(v).strip() and not validar_cnpj_valido(v):
            return v
        return v


class ResponsavelCompras(BaseModel):
    nome_responsavel: Optional[str] = None
    celular_responsavel: Optional[str] = None
    telefone_fixo_responsavel: Optional[str] = None
    email_resposavel: Optional[str] = None
    data_nascimento_resposavel: Optional[str] = None
    observacoes_responsavel: Optional[str] = None
    filial_resposavel: Optional[str] = None

    @field_validator("email_resposavel")
    @classmethod
    def email_valido(cls, v):
        if v and str(v).strip() and not validar_email(v):
            return v
        return v

    @field_validator("data_nascimento_resposavel")
    @classmethod
    def nascimento_valido(cls, v):
        if v and str(v).strip() and not validar_data_nascimento(v):
            return v
        return v

# Classes de Endereço de Faturamento

class EnderecoFaturamento(BaseModel):
    endereco_faturamento: Optional[str] = None
    bairro_faturamento: Optional[str] = None
    cep_faturamento: Optional[str] = None
    localizacao_faturamento: Optional[str] = None
    municipio_faturamento: Optional[str] = None
    estado_faturamento: Optional[str] = None
    email_danfe_faturamento: Optional[str] = None

#    @field_validator("email_danfe_faturamento")
#    def email_valido(cls, v):
#        if v and not validar_email(v):
#            raise ValueError("Email inválido")
#        return v

class RepresentanteLegal(BaseModel):
    nome_RepresentanteLegal: Optional[str] = None
    celular_RepresentanteLegal: Optional[str] = None
    email_RepresentanteLegal: Optional[str] = None
    data_nascimento_RepresentanteLegal: Optional[str] = None
    observacoes_RepresentanteLegal: Optional[str] = None
    
    @field_validator("email_RepresentanteLegal")
    @classmethod
    def email_valido(cls, v):
        if v and str(v).strip() and not validar_email(v):
            return v
        return v

    @field_validator("data_nascimento_RepresentanteLegal")
    @classmethod
    def nascimento_valido(cls, v):
        if v and str(v).strip() and not validar_data_nascimento(v):
            return v
        return v

# Classes de Endereço de Entrega

class EnderecoEntrega(BaseModel):
    endereco_EnderecoEntrega: Optional[str] = None
    bairro_EnderecoEntrega: Optional[str] = None
    cep_EnderecoEntrega: Optional[str] = None
    localizacao_EnderecoEntrega: Optional[str] = None
    municipio_EnderecoEntrega: Optional[str] = None
    estado_EnderecoEntrega: Optional[str] = None
    rota_principal_EnderecoEntrega: Optional[str] = None
    rota_de_aproximacao_EnderecoEntrega: Optional[str] = None
    observacao_motorista_EnderecoEntrega: Optional[str] = None

class ResponsavelRecebimento(BaseModel):
    nome_ResponsavelRecebimento: Optional[str] = None
    celular_ResponsavelRecebimento: Optional[str] = None
    email_ResponsavelRecebimento: Optional[str] = None
    data_nascimento_ResponsavelRecebimento: Optional[str] = None
    observacoes_ResponsavelRecebimento: Optional[str] = None


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
    endereco_EnderecoCobranca: Optional[str] = None
    bairro_EnderecoCobranca: Optional[str] = None
    cep_EnderecoCobranca: Optional[str] = None
    localizacao_EnderecoCobranca: Optional[str] = None
    municipio_EnderecoCobranca: Optional[str] = None
    estado_EnderecoCobranca: Optional[str] = None

class ResponsavelCobranca(BaseModel):
    nome_ResponsavelCobranca: Optional[str] = None
    celular_ResponsavelCobranca: Optional[str] = None
    email_ResponsavelCobranca: Optional[str] = None
    data_nascimento_ResponsavelCobranca: Optional[str] = None
    observacoes_ResponsavelCobranca: Optional[str] = None


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
    numero_danfe_Compras: Optional[str] = None
    emissao_Compras: Optional[str] = None
    valor_total_Compras: Optional[float] = None
    valor_frete_Compras: Optional[float] = None
    valor_frete_padrao_Compras: Optional[float] = None
    valor_ultimo_frete_to_Compras: Optional[float] = None
    lista_tabela_Compras: Optional[str] = None
    condicoes_pagamento_Compras: Optional[str] = None
    cliente_calcula_st_Compras: Optional[str] = None
    prazo_medio_compra_Compras: Optional[str] = None
    previsao_proxima_compra_Compras: Optional[str] = None

    @field_validator("emissao_Compras")
    @classmethod
    def data_emissao_valida(cls, v):
        if v and str(v).strip() and not validar_emissao(v):
            return v
        return v

    @field_validator(
        "valor_total_Compras",
        "valor_frete_Compras",
        "valor_frete_padrao_Compras",
        "valor_ultimo_frete_to_Compras"
    )
    @classmethod
    def valores_positivos(cls, v):
        if v is not None and not validar_valor_positivo(v):
            return v
        return v

class ObservacoesNaoCompra(BaseModel):
    observacoes_Compras: Optional[str] = None

# Classes de Elaboração do Cadastro

class DadosElaboracaoCadastro(BaseModel):
    classificacao_ElaboracaoCadastro: Optional[str] = None
    tipo_venda_prazo_ou_vista_ElaboracaoCadastro: Optional[str] = None
    limite_credito_ElaboracaoCadastro: Optional[float] = None
    data_vencimento_ElaboracaoCadastro: Optional[str] = None
    vendedor_ElaboracaoCadastro: Optional[str] = None
    gerente_insumos_ElaboracaoCadastro: Optional[str] = None
    gerente_pet_ElaboracaoCadastro: Optional[str] = None
    pre_posto_ElaboracaoCadastro: Optional[str] = None
    local_carregamento_ElaboracaoCadastro: Optional[str] = None

    @field_validator("data_vencimento_ElaboracaoCadastro")
    @classmethod
    def vencimento_valido(cls, v):
        if v and str(v).strip() and not validar_data_vencimento(v):
            return v
        return v

    @field_validator("limite_credito_ElaboracaoCadastro")
    @classmethod
    def limite_credito_valido(cls, v):
        if v is not None and not validar_valor_positivo(v):
            return v
        return v

class GrupoEconomico(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None

class ReferenciaComercial(BaseModel):
    empresa: Optional[str] = None
    cidade: Optional[str] = None
    telefone: Optional[str] = None
    contato: Optional[str] = None

class ReferenciaBancaria(BaseModel):
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta_corrente: Optional[str] = None
    gerente: Optional[str] = None
    contato_gerente: Optional[str] = None

class BemImovel(BaseModel):
    imovel: Optional[str] = None
    localizacao: Optional[str] = None
    area: Optional[str] = None
    valor: Optional[float] = None
    hipotecado: Optional[str] = None

class BemMovel(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    valor: Optional[float] = None
    alienado: Optional[str] = None

class PlantelAnimal(BaseModel):
    especie: Optional[str] = None
    numero_de_animais: Optional[int] = None
    consumo_diario: Optional[float] = None
    consumo_mensal: Optional[float] = None

    @model_validator(mode="after")
    def validar_consumo_animal(self):
        if self.consumo_diario and self.consumo_mensal:
            if not validar_consumo_coerente(self.consumo_diario, self.consumo_mensal):
                # Podemos logar um aviso ou apenas aceitar para não quebrar
                pass
        return self

class Supervisores(BaseModel):
    codigo_insumo_ElaboracaoCadastro: Optional[str] = None
    nome_insumos_ElaboracaoCadastro: Optional[str] = None
    codigo_pet_ElaboracaoCadastro: Optional[str] = None
    nome_pet_ElaboracaoCadastro: Optional[str] = None

class ComissaoDispet(BaseModel):
    insumos_ElaboracaoCadastro: Optional[str] = None
    pet_ElaboracaoCadastro: Optional[str] = None
    observacoes_ElaboracaoCadastro: Optional[str] = None

class CanalVendaCliente(BaseModel):
    canal_pet_ElaboracaoCadastro:     Optional[str] = None
    canal_frost_ElaboracaoCadastro:   Optional[str] = None
    canal_insumos_ElaboracaoCadastro: Optional[str] = None

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
    # Listas dinâmicas (JSONB)
    grupos_economicos: Optional[List[GrupoEconomico]] = []
    referencias_comerciais: Optional[List[ReferenciaComercial]] = []
    referencias_bancarias: Optional[List[ReferenciaBancaria]] = []
    bens_imoveis: Optional[List[BemImovel]] = []
    bens_moveis: Optional[List[BemMovel]] = []
    planteis_animais: Optional[List[PlantelAnimal]] = []
    # Indicacões (lista de até 5 strings)
    indicacoes_clientes: Optional[List[str]] = []
    supervisores: Optional[Supervisores] = None
    comissao_dispet: Optional[ComissaoDispet] = None
    canal_venda_cliente: Optional[CanalVendaCliente] = None

class ClienteResumo(BaseModel):
    id: int
    nome: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[str] = None
    ativo: Optional[bool] = None