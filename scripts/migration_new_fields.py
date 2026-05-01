import sys
import os

# Adiciona o diretório raiz ao path para encontrar o backend.database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Iniciando migrações...")
        
        # 1. Tabela Preço - campo observacao
        try:
            conn.execute(text("ALTER TABLE tb_tabela_preco ADD COLUMN observacao VARCHAR(100);"))
            print("Coluna 'observacao' adicionada à tb_tabela_preco.")
        except Exception as e:
            print(f"Erro ao adicionar 'observacao' ou coluna já existe: {e}")

        # 2. Pedidos - campos nota_fiscal e pedido_supra
        try:
            conn.execute(text("ALTER TABLE tb_pedidos ADD COLUMN nota_fiscal VARCHAR(50);"))
            print("Coluna 'nota_fiscal' adicionada à tb_pedidos.")
        except Exception as e:
            print(f"Erro ao adicionar 'nota_fiscal' ou coluna já existe: {e}")

        try:
            conn.execute(text("ALTER TABLE tb_pedidos ADD COLUMN pedido_supra VARCHAR(50);"))
            print("Coluna 'pedido_supra' adicionada à tb_pedidos.")
        except Exception as e:
            print(f"Erro ao adicionar 'pedido_supra' ou coluna já existe: {e}")
            
        # 3. Tabela Preço - campos para frete manual
        try:
            conn.execute(text("ALTER TABLE tb_tabela_preco ADD COLUMN manual_freight BOOLEAN DEFAULT FALSE;"))
            print("Coluna 'manual_freight' adicionada à tb_tabela_preco.")
        except Exception as e:
            print(f"Erro ao adicionar 'manual_freight' ou coluna já existe: {e}")

        conn.commit()
        print("Migrações concluídas com sucesso!")

if __name__ == "__main__":
    migrate()
