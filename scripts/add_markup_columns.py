
import os
import sys
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import DATABASE_URL

def add_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Adding markup columns...")
        
        # 1. Tabela Clientes
        try:
            print("1. Updating t_cadastro_cliente_v2...")
            conn.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN IF NOT EXISTS cadastro_markup FLOAT DEFAULT 0.0;"))
            print("   -> Success")
        except Exception as e:
            print(f"   -> Error: {e}")

        # 2. Tabela Preço
        try:
            print("2. Updating tb_tabela_preco...")
            conn.execute(text("ALTER TABLE tb_tabela_preco ADD COLUMN IF NOT EXISTS markup NUMERIC(9, 3) DEFAULT 0.0;"))
            print("   -> Success")
        except Exception as e:
            print(f"   -> Error: {e}")
            
        conn.commit()

if __name__ == "__main__":
    add_columns()
