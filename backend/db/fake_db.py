from datetime import datetime

clientes_db = [
  {
    "cadastrocliente": {
      "id": 1,
      "codigo_da_empresa": "EMP001",
      "ativo": True,
      "tipo_cliente": "Produtor Rural",
      "tipo_venda": "Venda Direta",
      "tipo_compra": "Consumo proprio",
      "limite_credito": 1500.0,
      "nome_cliente": "Cliente 1",
      "nome_fantasia": "Fantasia 1",
      "cnpj": "64.229.098/0001-20",
      "inscricao_estadual": "ISENTO",
      "cpf": "123.456.789-09",
      "situacao": "ATIVO",
      "indicacao_cliente": "Cliente Antigo",
      "ramo_de_atividade": "BOVINO CORTE",
      "atividade_principal": "BOVINO CONFINAMENTO"
    },
    "responsavel_compras": {
      "nome_responsavel": "Maria Compras",
      "celular_responsavel": "(11)91234-5678",
      "email_resposavel": "maria@compras.com",
      "data_nascimento_resposavel": "1980-01-01",
      "observacoes_responsavel": "Atende pela manha",
      "filial_resposavel": "Filial 01"
    },
    "endereco_faturamento": {
      "endereco_faturamento": "Rua Faturamento 1",
      "bairro_faturamento": "Centro",
      "cep_faturamento": "00000-000",
      "localizacao_faturamento": "GPS XYZ",
      "municipio_faturamento": "São Paulo",
      "estado_faturamento": "SP",
      "email_danfe_faturamento": "financeiro@fazenda.com"
    },
    "data_criacao": "2025-07-16T21:13:53.360517",
    "data_atualizacao": "2025-07-16T21:13:53.360528",
  },
  {
    "cadastrocliente": {
      "id": 2,
      "codigo_da_empresa": "EMP002",
      "ativo": False,
      "tipo_cliente": "Produtor Rural",
      "tipo_venda": "Venda Direta",
      "tipo_compra": "Consumo proprio",
      "limite_credito": 1500.0,
      "nome_cliente": "Cliente 2",
      "nome_fantasia": "Fantasia 2",
      "cnpj": "90.458.633/0001-68",
      "inscricao_estadual": "ISENTO",
      "cpf": "987.654.321-00",
      "situacao": "ATIVO",
      "indicacao_cliente": "Cliente Antigo",
      "ramo_de_atividade": "BOVINO CORTE",
      "atividade_principal": "BOVINO CONFINAMENTO"
    },
    "responsavel_compras": {
      "nome_responsavel": "Maria Compras",
      "celular_responsavel": "(11)91234-5678",
      "email_resposavel": "maria@compras.com",
      "data_nascimento_resposavel": "1980-01-01",
      "observacoes_responsavel": "Atende pela manha",
      "filial_resposavel": "Filial 01"
    },
    "endereco_faturamento": {
      "endereco_faturamento": "Rua Faturamento 1",
      "bairro_faturamento": "Centro",
      "cep_faturamento": "00000-000",
      "localizacao_faturamento": "GPS XYZ",
      "municipio_faturamento": "São Paulo",
      "estado_faturamento": "MG",
      "email_danfe_faturamento": "financeiro@fazenda.com"
    },
    "data_criacao": "2025-07-16T21:13:53.360517",
    "data_atualizacao": "2025-07-16T21:13:53.360528",
    
  },
  {
    "cadastrocliente": {
      "id": 3,
      "codigo_da_empresa": "EMP003",
      "ativo": True,
      "tipo_cliente": "Produtor Rural",
      "tipo_venda": "Venda Direta",
      "tipo_compra": "Consumo proprio",
      "limite_credito": 1500.0,
      "nome_cliente": "Cliente 3",
      "nome_fantasia": "Fantasia 3",
      "cnpj": "12345678000195",
      "inscricao_estadual": "ISENTO",
      "cpf": "11144477735",
      "situacao": "ATIVO",
      "indicacao_cliente": "Cliente Antigo",
      "ramo_de_atividade": "BOVINO CORTE",
      "atividade_principal": "BOVINO CONFINAMENTO"
    },
    "responsavel_compras": {
      "nome_responsavel": "Maria Compras",
      "celular_responsavel": "(11)91234-5678",
      "email_resposavel": "maria@compras.com",
      "data_nascimento_resposavel": "1980-01-01",
      "observacoes_responsavel": "Atende pela manha",
      "filial_resposavel": "Filial 01"
    },
    "endereco_faturamento": {
      "endereco_faturamento": "Rua Faturamento 1",
      "bairro_faturamento": "Centro",
      "cep_faturamento": "00000-000",
      "localizacao_faturamento": "GPS XYZ",
      "municipio_faturamento": "São Paulo",
      "estado_faturamento": "PR",
      "email_danfe_faturamento": "financeiro@fazenda.com"
    },
    "data_criacao": "2025-07-16T21:13:53.360517",
    "data_atualizacao": "2025-07-16T21:13:53.360528",
    
  },
  {
    "cadastrocliente": {
      "id": 4, 
      "codigo_da_empresa": "EMP004",
      "ativo": False,
      "tipo_cliente": "Produtor Rural",
      "tipo_venda": "Venda Direta",
      "tipo_compra": "Consumo proprio",
      "limite_credito": 1500.0,
      "nome_cliente": "Cliente 4",
      "nome_fantasia": "Fantasia 4",
      "cnpj": "77.132.874/0001-81",
      "inscricao_estadual": "ISENTO",
      "cpf": "741.852.963-20",
      "situacao": "ATIVO",
      "indicacao_cliente": "Cliente Antigo",
      "ramo_de_atividade": "BOVINO CORTE",
      "atividade_principal": "BOVINO CONFINAMENTO"
    },
    "responsavel_compras": {
      "nome_responsavel": "Maria Compras",
      "celular_responsavel": "(11)91234-5678",
      "email_resposavel": "maria@compras.com",
      "data_nascimento_resposavel": "1980-01-01",
      "observacoes_responsavel": "Atende pela manha",
      "filial_resposavel": "Filial 01"
    },
    "endereco_faturamento": {
      "endereco_faturamento": "Rua Faturamento 1",
      "bairro_faturamento": "Centro",
      "cep_faturamento": "00000-000",
      "localizacao_faturamento": "GPS XYZ",
      "municipio_faturamento": "São Paulo",
      "estado_faturamento": "SP",
      "email_danfe_faturamento": "financeiro@fazenda.com"
    },
    "data_criacao": "2025-07-16T21:13:53.360517",
    "data_atualizacao": "2025-07-16T21:13:53.360528",
    
  },
  {
    "cadastrocliente": {
      "id": 5,
      "codigo_da_empresa": "EMP005",
      "ativo": True,
      "tipo_cliente": "Produtor Rural",
      "tipo_venda": "Venda Direta",
      "tipo_compra": "Consumo proprio",
      "limite_credito": 1500.0,
      "nome_cliente": "Cliente 5",
      "nome_fantasia": "Fantasia 5",
      "cnpj": "01.001.001/0001-00",
      "inscricao_estadual": "ISENTO",
      "cpf": "456.123.789-12",
      "situacao": "ATIVO",
      "indicacao_cliente": "Cliente Antigo",
      "ramo_de_atividade": "BOVINO CORTE",
      "atividade_principal": "BOVINO CONFINAMENTO"
    },
    "responsavel_compras": {
      "nome_responsavel": "Maria Compras",
      "celular_responsavel": "(11)91234-5678",
      "email_resposavel": "maria@compras.com",
      "data_nascimento_resposavel": "1980-01-01",
      "observacoes_responsavel": "Atende pela manha",
      "filial_resposavel": "Filial 01"
    },
    "endereco_faturamento": {
      "endereco_faturamento": "Rua Faturamento 1",
      "bairro_faturamento": "Centro",
      "cep_faturamento": "00000-000",
      "localizacao_faturamento": "GPS XYZ",
      "municipio_faturamento": "São Paulo",
      "estado_faturamento": "MG",
      "email_danfe_faturamento": "financeiro@fazenda.com"
    },
    "data_criacao": "2025-07-16T21:13:53.360517",
    "data_atualizacao": "2025-07-16T21:13:53.360528",
    
  }
]
