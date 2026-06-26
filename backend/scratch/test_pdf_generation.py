import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from services.pedido_pdf_data import carregar_pedido_pdf
from services.pdf_service import gerar_pdf_pedido
from models.pedido_pdf import PedidoPdf, PedidoPdfItem
from datetime import datetime

# Build a mock order to test PDF client layout directly
mock_item = PedidoPdfItem(
    codigo="1001",
    produto="Produto Teste para Cabeçalho PDF",
    embalagem="SC 25KG",
    quantidade=5.0,
    condicao_pagamento="30 DIAS",
    tabela_comissao="Fator 1",
    valor_retira=10.0,
    valor_entrega=12.0,
    peso_liquido_total=0.0
)

mock_pedido = PedidoPdf(
    id_pedido=9999,
    codigo_cliente="1234",
    cliente="CLIENTE TESTE PDF HEADERS",
    nome_fantasia="FANTASIA TESTE",
    data_pedido=datetime.now(),
    data_entrega_ou_retirada=datetime.now(),
    frete_total=100.0,
    frete_kg=0.20,
    validade_tabela="2026-12-31",
    total_peso_bruto=125.0,
    total_peso_liquido=125.0,
    total_valor=60.0,
    observacoes="Observações de teste para o cabeçalho",
    itens=[mock_item]
)

# Test with com frete (should output 'C/ frete' header)
mock_pedido.usar_valor_com_frete = True
pdf_bytes_cf = gerar_pdf_pedido(mock_pedido, sem_validade=True)
print(f"Generated PDF c/ frete (simplified layout): {len(pdf_bytes_cf)} bytes")

# Test with sem frete (should output 'S/ frete' header)
mock_pedido.usar_valor_com_frete = False
pdf_bytes_sf = gerar_pdf_pedido(mock_pedido, sem_validade=True)
print(f"Generated PDF s/ frete (simplified layout): {len(pdf_bytes_sf)} bytes")

print("All tests completed successfully!")
