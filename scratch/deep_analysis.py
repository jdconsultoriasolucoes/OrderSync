import re

def analyze():
    # Read FICHA RECADASTRO V.2026-2.xls structure
    xls_fields = [
        "Nome do Cliente (Razão Social)",
        "Denominação Comercial/Fantasia",
        "Telefone",
        "Celular",
        "E-mail",
        "CNPJ",
        "CPF",
        "INSCR. PRODUTOR (Inscrição Produtor Rural)",
        "INSCR. ESTADUAL (Inscrição Estadual)",
        "OBSERVAÇÕES",
        "Utilização do Produto (Insumo Pecuária / Consumo Próprio / Industrialização / Revender)",
        "Endereço de Entrega - Av/Rua/Nro.",
        "Endereço de Entrega - Bairro",
        "Endereço de Entrega - CEP",
        "Endereço de Entrega - Cidade",
        "Endereço de Entrega - Estado",
        "Endereço de Cobrança - Av/Rua/Nro.",
        "Endereço de Cobrança - Bairro",
        "Endereço de Cobrança - CEP",
        "Endereço de Cobrança - Cidade",
        "Endereço de Cobrança - Estado",
        "LIMITE APROVADO (R$)",
        "LIMITE SOLICITADO (R$)",
        "Referências Bancárias 1..3 - Banco",
        "Referências Bancárias 1..3 - Agência",
        "Referências Bancárias 1..3 - Conta Corrente",
        "Referências Bancárias 1..3 - Cidade",
        "Referências Bancárias 1..3 - Telefone",
        "Referências Bancárias 1..3 - Contato",
        "Canal de Vendas - PET (Classe / Canal)",
        "Canal de Vendas - FROST (Classe / Canal)",
        "Canal de Vendas - INSUMOS (Classe / Canal)",
        "Atendimento Distribuidor/Revendedor/Agente - PET (Código e Razão Social)",
        "Atendimento Distribuidor/Revendedor/Agente - FROST (Código e Razão Social)",
        "Atendimento Distribuidor/Revendedor/Agente - INSUMOS (Código e Razão Social)",
        "Vistos / Equipe - Vendedor/Supervisor Nome (Linha Pet)",
        "Vistos / Equipe - Vendedor/Supervisor Código (Linha Pet)",
        "Vistos / Equipe - Vendedor/Supervisor Nome (Linha Insumos)",
        "Vistos / Equipe - Vendedor/Supervisor Código (Linha Insumos)",
        "Vistos / Equipe - Gerente Vendas Nome (Linha Pet)",
        "Vistos / Equipe - Gerente Vendas Nome (Linha Insumos)",
        "Local e Data",
        "Assinatura do Cliente",
        "Assinatura do Representante Alisul"
    ]

    with open(r'e:\OrderSync\frontend\public\clientes\cliente.html', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    print("=== SEARCHING HTML FOR FIELD MATCHES ===")
    for field in xls_fields:
        print(f"Field: {field}")

analyze()
