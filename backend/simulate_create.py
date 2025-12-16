
import sys
import os
# Adiciona o diretório atual ao path para importar módulos do backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from schemas.produto import ProdutoV2Create, ImpostoV2Create
from services.produto_pdf import create_produto

def simulate():
    print("--- Simulando Criação de Produto ---")
    db = SessionLocal()
    try:
        # Dados do Produto (Payload)
        # Note: status_produto é obrigatório pelo Schema Base
        novo_produto = ProdutoV2Create(
            codigo_supra="PROD_TESTE_01",
            nome_produto="Produto Teste Simulação",
            preco=150.50,
            preco_tonelada=3500.00,
            status_produto="ATIVO", 
            familia="ARGAMASSAS" # Agora aceita texto!
        )
        
        # Dados de Imposto (Opcional, mas bom pra teste completo)
        novo_imposto = ImpostoV2Create(
            ipi=0.0,
            icms=18.0,
            iva_st=0.0
        )

        print(f"Tentando criar produto: {novo_produto.codigo_supra} - {novo_produto.nome_produto}")
        
        resultado = create_produto(db, novo_produto, novo_imposto)
        
        print("\nSUCESSO!")
        print(f"ID Gerado: {resultado.id}")
        print(f"Nome: {resultado.nome_produto}")
        print(f"Preço: R$ {resultado.preco}")
        print(f"Preço Ton: R$ {resultado.preco_tonelada}")
        print(f"Família: {resultado.familia}")
        
    except Exception as e:
        print("\nERRO ao criar produto:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    simulate()
