from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, BigInteger
from database import Base

class ClienteModel(Base):
    __tablename__ = "t_cadastro_cliente"

    # Primary Key
    codigo = Column(BigInteger, primary_key=True, index=True)

    # Identification
    nome_empresarial = Column(String)
    nome_fantasia = Column(String)
    tipo_pessoa = Column(String)
    ramo_juridico = Column(String)
    atividade_principal = Column(String)
    ativo_nao_ativo = Column(String)
    ocorrencia = Column(String)

    # Contact
    contato_comprador = Column(String)
    telefone_contato = Column(String)
    email_contato = Column(String)

    # Billing Address (Faturamento)
    retira_sim_nao_faturamento = Column(String)
    endereco_faturamento = Column(String)
    numero_faturamento = Column(String)
    bairro_faturamento = Column(String)
    cep_faturamento = Column(String)
    cidade_faturamento = Column(String)
    uf_faturamento = Column(String)
    cnpj_cpf_faturamento = Column(String)
    inscricao_estadual_faturamento = Column(String)
    telefone_faturamento = Column(String)
    e_mail_faturamento = Column("e-mail_faturamento", String)

    # Delivery Address (Entrega)
    cidade_entrega = Column(String)
    km_entrega = Column(BigInteger)
    rota_entrega = Column(BigInteger)
    id_entrega = Column(BigInteger)
    sugestao_de_frete_to_entrega = Column(Float)
    endereco_entrega = Column(String)
    observacao_entrega = Column(String)
    contato_entrega = Column(String)
    telefone_entrega = Column(String)
    e_mail_entrega = Column("e-mail_entrega", String)
    mensagem_faturamento_entrega = Column(String)
    mensagem_motorista_entrega = Column(String)
    
    # Billing Contact (Cobrança)
    contato_cobranca = Column(String)
    telefone_cobranca = Column(String)
    email_cobranca = Column(String)
    cidade_cobranca = Column(String)
    endereco_cobranca = Column(String)

    # Alisul Specific
    supervisor_alisul = Column(String)
    tipo_de_cliente_alisul = Column(String)
    data_ocorrencia_alisul = Column(DateTime)
    observacoes_alisul_1 = Column(String)
    observacoes_alisul_2 = Column(String)

    # Formatted / Derived
    bairro_faturamento_formatted = Column(String)
    cidade_faturamento_formatted = Column(String)
    cnpj_cpf_faturamento_formatted = Column(String)
    cidade_entrega_formatted = Column(String)
    cidade_cobranca_formatted = Column(String)
    
    # Removed data_criacao and data_atualizacao as they don't exist in DB schema
