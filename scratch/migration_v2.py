
import sys
import os

# Adiciona o diretório backend ao path para importar database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

try:
    from database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        print("Adicionando frete_base_ton à tabela tb_pedidos_itens...")
        try:
            conn.execute(text("ALTER TABLE public.tb_pedidos_itens ADD COLUMN IF NOT EXISTS frete_base_ton FLOAT DEFAULT 0.0"))
            conn.execute(text("ALTER TABLE public.tb_tabela_preco ADD COLUMN IF NOT EXISTS frete_base_ton FLOAT DEFAULT 0.0"))
            conn.commit()
            print("Sucesso: Coluna frete_base_ton adicionada às tabelas relevantes.")
        except Exception as e:
            print(f"Erro ao adicionar coluna: {e}")
            
except Exception as e:
    print(f"Erro ao conectar ou importar: {e}")
