import sys
import os
from sqlalchemy import text

# Adiciona o diretório atual ao path para importar modulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal

def inspeccionar_link(code):
    print(f"--- Inspecionando Link: {code} ---")
    
    db = SessionLocal()
    try:
        # 1. Buscar dados do Link
        query_link = text("""
            SELECT code, tabela_id, codigo_cliente, created_at, expires_at 
            FROM tb_pedido_link 
            WHERE code = :code
        """)
        link_row = db.execute(query_link, {"code": code}).mappings().first()
        
        if not link_row:
            print(f"ERRO: Link '{code}' não encontrado no banco de dados.")
            return

        print(f"[LINK] Tabela ID: {link_row['tabela_id']}")
        print(f"[LINK] Cliente Code (no link): '{link_row['codigo_cliente']}'")
        print(f"[LINK] Criado em: {link_row['created_at']}")
        
        # 2. Buscar dados da Tabela associada
        tabela_id = link_row['tabela_id']
        query_tabela = text("""
            SELECT id_tabela, nome_tabela, codigo_cliente, cliente, fornecedor 
            FROM tb_tabela_preco 
            WHERE id_tabela = :tid 
            LIMIT 1
        """)
        tabela_row = db.execute(query_tabela, {"tid": tabela_id}).mappings().first()
        
        if not tabela_row:
             print(f"ERRO: Tabela de Preço ID {tabela_id} não encontrada!")
             return

        print(f"[TABELA] Nome: {tabela_row['nome_tabela']}")
        print(f"[TABELA] Cliente Check: '{tabela_row['cliente']}'")
        print(f"[TABELA] Código Cliente (na tabela): '{tabela_row['codigo_cliente']}'")
        
        # 3. Diagnóstico
        cod_link = str(link_row['codigo_cliente'] or "").strip()
        cod_tab  = str(tabela_row['codigo_cliente'] or "").strip()
        
        if cod_link and cod_link != "Não cadastrado":
            print("\n=> DIAGNÓSTICO: O Link tem o código. O pedido deveria funcionar.")
        elif cod_tab and cod_tab != "Não cadastrado":
            print("\n=> DIAGNÓSTICO: O Link NÃO tem o código, mas a Tabela TEM.")
            print("   A correção 'Fallback 2' (já aplicada) DEVE fazer funcionar.")
        else:
            print("\n=> DIAGNÓSTICO: Nem o Link nem a Tabela original possuem o código do cliente.")
            print("   Isso significa que a Tabela de Preço foi criada sem vincular o código corretamente.")
            print("   Solução: É necessário criar uma NOVA Tabela de Preço garantindo que o cliente foi selecionado corretamente.")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        db.close()
        print("--- Fim ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python debug_link_info.py <CODIGO_DO_LINK_SEM_URL>")
        print("Exemplo: python debug_link_info.py ABC_123_XYZ")
        sys.exit(1)
    
    code = sys.argv[1]
    # Remove URL part if user pasted full link
    if "/p/" in code:
        code = code.split("/p/")[1].split("?")[0]
        
    inspeccionar_link(code)
