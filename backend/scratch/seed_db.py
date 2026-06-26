import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from models.produto import ProdutoV2, HistoricoEstoqueV2
from datetime import date

with SessionLocal() as db:
    # 1. Clean existing records
    db.query(TabelaPrecoModel).delete()
    db.query(ProdutoV2).delete()
    db.query(HistoricoEstoqueV2).delete()
    db.commit()

    # 2. Create products
    p1 = ProdutoV2(
        id=1,
        codigo_supra="1001",
        status_produto="ATIVO",
        nome_produto="Produto Teste A",
        fornecedor="SUPRA ALIMENTOS",
        estoque_disponivel=50,
        estoque_futuro=100,
        validade_tabela=date(2026, 12, 31),
        nome_arquivo_estoque="estoque_vigente.xlsx"
    )
    p2 = ProdutoV2(
        id=2,
        codigo_supra="1002",
        status_produto="ATIVO",
        nome_produto="Produto Teste B",
        fornecedor="SUPRA ALIMENTOS",
        estoque_disponivel=10,
        estoque_futuro=20,
        validade_tabela=date(2026, 12, 31),
        nome_arquivo_estoque="estoque_vigente.xlsx"
    )
    p3 = ProdutoV2(
        id=3,
        codigo_supra="1003",
        status_produto="ATIVO",
        nome_produto="Produto Teste C",
        fornecedor="SUPRA",  # Supplier name differs
        estoque_disponivel=15,
        estoque_futuro=30,
        validade_tabela=date(2026, 12, 31),
        nome_arquivo_estoque="estoque_vigente.xlsx"
    )
    db.add_all([p1, p2, p3])
    db.commit()

    # 3. Create price table items
    # In table price table ID = 1
    t1 = TabelaPrecoModel(
        id_linha=1,
        id_tabela=1,
        nome_tabela="Tabela Teste 1",
        fornecedor="SUPRA ALIMENTOS",
        cliente="Cliente Teste",
        codigo_produto_supra="1001",
        descricao_produto="Produto Teste A",
        embalagem="SC 25KG",
        peso_liquido=25.000,
        valor_produto=100.00,
        descricao_fator_comissao="Fator 1",
        codigo_plano_pagamento="30d",
        valor_frete=5.00,
        valor_s_frete=95.00,
        grupo="Grupo A",
        departamento="Depto B",
        ipi=0.00,
        icms_st=0.00,
        iva_st=0.00,
        ativo=True
    )
    t2 = TabelaPrecoModel(
        id_linha=2,
        id_tabela=1,
        nome_tabela="Tabela Teste 1",
        fornecedor="SUPRA ALIMENTOS",
        cliente="Cliente Teste",
        codigo_produto_supra="1002",
        descricao_produto="Produto Teste B",
        embalagem="SC 25KG",
        peso_liquido=25.000,
        valor_produto=120.00,
        descricao_fator_comissao="Fator 1",
        codigo_plano_pagamento="30d",
        valor_frete=5.00,
        valor_s_frete=115.00,
        grupo="Grupo A",
        departamento="Depto B",
        ipi=0.00,
        icms_st=0.00,
        iva_st=0.00,
        ativo=True
    )
    t3 = TabelaPrecoModel(
        id_linha=3,
        id_tabela=1,
        nome_tabela="Tabela Teste 1",
        fornecedor="SUPRA ALIMENTOS",  # Supplier in price table is SUPRA ALIMENTOS, but product p3 has supplier SUPRA
        cliente="Cliente Teste",
        codigo_produto_supra="1003",
        descricao_produto="Produto Teste C",
        embalagem="SC 25KG",
        peso_liquido=25.000,
        valor_produto=150.00,
        descricao_fator_comissao="Fator 1",
        codigo_plano_pagamento="30d",
        valor_frete=5.00,
        valor_s_frete=145.00,
        grupo="Grupo A",
        departamento="Depto B",
        ipi=0.00,
        icms_st=0.00,
        iva_st=0.00,
        ativo=True
    )
    db.add_all([t1, t2, t3])
    db.commit()

    # 4. Create active stock history
    h1 = HistoricoEstoqueV2(
        id=1,
        codigo_supra="1001",
        nome_produto="Produto Teste A",
        estoque_disponivel=50,
        estoque_futuro=100,
        nome_arquivo="estoque_vigente.xlsx",
        ativo=True
    )
    h2 = HistoricoEstoqueV2(
        id=2,
        codigo_supra="1002",
        nome_produto="Produto Teste B",
        estoque_disponivel=10,
        estoque_futuro=20,
        nome_arquivo="estoque_vigente.xlsx",
        ativo=True
    )
    # Stock history for 1003
    h3 = HistoricoEstoqueV2(
        id=3,
        codigo_supra="1003",
        nome_produto="Produto Teste C",
        estoque_disponivel=15,
        estoque_futuro=30,
        nome_arquivo="estoque_vigente.xlsx",
        ativo=True
    )
    db.add_all([h1, h2, h3])
    db.commit()

print("Seeding database complete!")
