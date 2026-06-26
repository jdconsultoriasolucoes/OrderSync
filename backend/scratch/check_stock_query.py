import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from models.produto import ProdutoV2, HistoricoEstoqueV2

with SessionLocal() as db:
    # Get first price table
    tabela = db.query(TabelaPrecoModel).filter_by(ativo=True).first()
    if not tabela:
        print("Nenhuma tabela de preço ativa encontrada no banco local!")
    else:
        print(f"Tabela de preço encontrada: ID {tabela.id_tabela}, Nome: {tabela.nome_tabela}, Fornecedor: '{tabela.fornecedor}'")
        itens = db.query(TabelaPrecoModel).filter_by(id_tabela=tabela.id_tabela, ativo=True).all()
        print(f"Total de itens na tabela: {len(itens)}")
        
        # Test query
        codigos = [i.codigo_produto_supra for i in itens if i.codigo_produto_supra]
        print(f"Primeiros 5 códigos de produto na tabela: {codigos[:5]}")
        
        # Search for these products in t_cadastro_produto_v2
        prod_count = db.query(ProdutoV2).filter(ProdutoV2.codigo_supra.in_(codigos)).count()
        print(f"Quantidade de produtos encontrados em t_cadastro_produto_v2: {prod_count}")
        
        # Check supplier matching
        prod_fornecedor_match = db.query(ProdutoV2).filter(
            ProdutoV2.codigo_supra.in_(codigos),
            ProdutoV2.fornecedor == tabela.fornecedor
        ).count()
        print(f"Quantidade de produtos com fornecedor idêntico ('{tabela.fornecedor}'): {prod_fornecedor_match}")
        
        # Check distinct suppliers in t_cadastro_produto_v2 for these codes
        suppliers = db.query(ProdutoV2.fornecedor).filter(ProdutoV2.codigo_supra.in_(codigos)).distinct().all()
        print(f"Fornecedores encontrados para estes códigos na tabela de produtos: {[s[0] for s in suppliers]}")
        
        # Let's inspect some active stocks
        active_stocks = db.query(HistoricoEstoqueV2).filter_by(ativo=True).limit(5).all()
        print("Registros de estoque ativo (primeiros 5):")
        for st in active_stocks:
            print(f"  Código: {st.codigo_supra}, Arquivo: {st.nome_arquivo}, Qtd: {st.estoque_disponivel}, Ativo: {st.ativo}")
