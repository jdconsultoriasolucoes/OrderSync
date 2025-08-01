import pytest
from fastapi.testclient import TestClient
from main import app
from services.tabela_preco import calcular_valor_liquido

client = TestClient(app)

# 🔹 Teste de função (unitário)
def test_calcular_valor_liquido():
    resultado = calcular_valor_liquido(100.0, 0.1, 0.05)
    assert round(resultado["acrescimo"], 4) == 10.0
    assert round(resultado["desconto"], 4) == 5.0
    assert round(resultado["valor_liquido"], 2) == 105.0


# 🔹 Teste de rota (integração)
def test_get_produtos_filtro():
    response = client.get("/tabela_preco/produtos_filtro", params={
        "grupo": "Rações",
        "plano_pagamento": "921",
        "frete_kg": 2.5,
        "fator_comissao": 0.05
    })
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if response.json():
        produto = response.json()[0]
        assert "valor" in produto
        assert "valor_liquido" in produto
        assert "fator_comissao" in produto
