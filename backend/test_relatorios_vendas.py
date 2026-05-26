import sys
import os
# Define o banco de dados padrão para testes locais se não estiver presente no ambiente
os.environ.setdefault("DATABASE_URL", "postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from routers.relatorios import get_vendas_cliente_filtros, get_vendas_cliente, get_vendas_produtos

def test_endpoints():
    print("Iniciando testes nos novos endpoints de Relatórios de Vendas...")
    db = SessionLocal()
    try:
        # 1. Testando metadados de filtros
        print("\n1. Chamando get_vendas_cliente_filtros()...")
        filtros = get_vendas_cliente_filtros(db)
        print(" -> Sucesso!")
        print(f" -> Filiais encontradas: {len(filtros.get('filiais', []))} -> {filtros.get('filiais')}")
        print(f" -> Status encontrados: {len(filtros.get('status', []))} -> {filtros.get('status')}")
        print(f" -> Municípios encontrados: {len(filtros.get('municipios', []))} -> {filtros.get('municipios')[:5]}...")
        print(f" -> Grupos de produtos encontrados: {len(filtros.get('grupos', []))} -> {filtros.get('grupos')[:5]}...")

        # 2. Testando listagem geral de vendas por cliente
        print("\n2. Chamando get_vendas_cliente() sem filtros...")
        vendas = get_vendas_cliente(db=db)
        print(" -> Sucesso!")
        print(f" -> Total de registros de vendas de clientes carregados: {len(vendas)}")
        if len(vendas) > 0:
            v0 = vendas[0]
            print("\nEstrutura do primeiro registro de cliente retornado:")
            for k, v in v0.items():
                print(f" - {k}: {v} ({type(v).__name__})")

        # 3. Testando listagem geral de vendas por produto
        print("\n3. Chamando get_vendas_produtos() sem filtros...")
        produtos = get_vendas_produtos(db=db)
        print(" -> Sucesso!")
        print(f" -> Total de registros de produtos vendidos carregados: {len(produtos)}")
        if len(produtos) > 0:
            p0 = produtos[0]
            print("\nEstrutura do primeiro registro de produto retornado:")
            for k, v in p0.items():
                print(f" - {k}: {v} ({type(v).__name__})")

        # 4. Testando listagem de produtos com filtros de grupo/marca
        if len(filtros.get('grupos', [])) > 0:
            grupo_teste = [filtros['grupos'][0]]
            print(f"\n4. Chamando get_vendas_produtos() com filtro de grupo: {grupo_teste}...")
            prod_filtrados = get_vendas_produtos(grupos=grupo_teste, db=db)
            print(" -> Sucesso!")
            print(f" -> Total de produtos filtrados no grupo {grupo_teste}: {len(prod_filtrados)}")

        print("\nTodos os testes de backend concluídos com sucesso!")
    except Exception as e:
        print(f"\nERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
