import re

with open(r'e:\OrderSync\frontend\public\clientes\cliente.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

with open(r'e:\OrderSync\backend\models\cliente_v2.py', 'r', encoding='utf-8', errors='ignore') as f:
    py_model = f.read()

print("=== CHECKING FIELDS IN SYSTEM ===")
# Check specific fields
fields_to_check = [
    'tipo_cliente_checkboxes', # Revendedor, Cli Direto, Redes, Clínica Vet, Lojista, Atacado, Peq. S.M., Pet Shop
    'contatos_internos', # C/Vendas, P/Cobranças
    'ref_bancaria_cidade',
    'ref_bancaria_telefone',
    'ref_bancaria_contato',
    'ref_comercial', # Empresa, Cidade, Telefone, Contato
    'bens_imoveis', # Imovel, Localizacao, Area, Valor, Hipotecado
    'planteis_animais', # Especie, No Animais, Consumo Diario, Consumo Mensal
    'bens_moveis', # Marca, Modelo, Valor, Alienado
    'utilizacao_produto', # Insumos na Pecuaria, Consumo Proprio, Industrializacao, Revender
    'locais_carregamento',
    'lista_preco_canal',
    'analise_credito_negativas', # Negativas, Judicial
    'forma_pagamento_vendor_cobranca', # Vendor / Cobrança
    'restricoes_credito'
]

print("Model fields count:", len(py_model.splitlines()))
