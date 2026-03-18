
import sys
import os

# Adiciona o diretório backend ao path para importar o database
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import text
from database import SessionLocal

def test_queries():
    db = SessionLocal()
    try:
        print("--- Verificando Tabelas ---")
        sql_tables = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = db.execute(sql_tables).fetchall()
        for t in tables:
            res = db.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
            print(f"Tabela: {t[0]} | Registros: {res}")

        print("\n--- Testando Query de Cargas Pedidos Detalhes ---")
        sql_relatorios = text("""
            SELECT 
                p.id_pedido,
                p.codigo_cliente,
                p.cliente AS cliente_original,
                COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente_nome_atualizado
            FROM tb_pedidos p
            LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
            LIMIT 5
        """)
        rows = db.execute(sql_relatorios).mappings().all()
        for r in rows:
            print(f"Pedido: {r['id_pedido']} | Original: {r['cliente_original']} | Atualizado: {r['cliente_nome_atualizado']}")
            
        print("\n--- Testando Query de Listagem de Pedidos ---")
        sql_pedidos = text("""
            SELECT
              a.id_pedido,
              a.cliente AS cliente_original,
              COALESCE(c.cadastro_nome_cliente, a.cliente) AS cliente_nome_atualizado
            FROM public.tb_pedidos a
            LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = a.codigo_cliente
            LIMIT 5
        """)
        rows = db.execute(sql_pedidos).mappings().all()
        for r in rows:
            print(f"Pedido: {r['id_pedido']} | Original: {r['cliente_original']} | Atualizado: {r['cliente_nome_atualizado']}")

    except Exception as e:
        print(f"Erro ao testar queries: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_queries()
